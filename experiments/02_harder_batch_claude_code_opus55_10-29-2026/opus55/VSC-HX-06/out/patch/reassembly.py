# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Recipient-side reassembly of fragmented messages.

The recipient keeps one buffer per message.  A fragment can reach the
recipient more than once: when the link loses the acknowledgement of a
received fragment the sender retries it.  The message is complete when the
buffer holds every fragment 1..n; the body is the fragments in index order.
"""


class Buffer:
    def __init__(self, count, size):
        self.count = count        # number of fragments of the message
        self.size = size          # declared body size in bytes
        self.parts = {}
        self.received = 0         # distinct bytes received so far

    def add(self, index, data):
        """Store fragment INDEX; True if the message is now complete."""
        if index not in self.parts:
            self.parts[index] = data
            self.received += len(data)
        return len(self.parts) == self.count

    def missing(self):
        return [i for i in range(1, self.count + 1) if i not in self.parts]

    def assemble(self):
        return b"".join(self.parts[i] for i in sorted(self.parts))

    def progress(self):
        return "%d/%d" % (len(self.parts), self.count)
