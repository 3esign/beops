"""A pipe-owned lease on Svemir's existing Ollama mutex, released when the parent dies."""
import contextlib
import json
import pathlib
import queue
import subprocess
import threading


class CapacityBusy(TimeoutError):
    pass


@contextlib.contextmanager
def receipt_scope(receipt, destination, publish):
    """A capacity stop preserves partial progress and emits a waiting receipt."""
    try:
        yield
    except CapacityBusy as exc:
        receipt.update(state='waiting_model', reason=str(exc))
        publish(destination, receipt)


@contextlib.contextmanager
def shared_slot(timeout):
    process = None
    try:
        process = subprocess.Popen(['node', str(pathlib.Path(__file__).with_name('model_lease.js')),
                                    str(int(min(30, max(0, timeout)) * 1000))],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8',
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        messages = queue.Queue()
        threading.Thread(target=lambda: messages.put(process.stdout.readline()), daemon=True).start()
        try:
            message = json.loads(messages.get(timeout=max(0, timeout) + 5))
        except (queue.Empty, ValueError) as exc:
            raise CapacityBusy('shared Ollama coordinator unavailable') from exc
        if message.get('state') != 'acquired':
            raise CapacityBusy('shared Ollama capacity ' + message.get('state', 'unavailable'))
        yield message
    except OSError as exc:
        if process is None:
            raise CapacityBusy('shared Ollama coordinator could not start') from exc
        raise
    finally:
        if process is not None:
            try:
                process.stdin.close()
            except (OSError, BrokenPipeError):
                pass
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            process.stdout.close()
            process.stderr.close()
