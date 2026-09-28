def enqueue(q, item):
    return q + (item,)
def dequeue(q):
    return q[0], q[1:] if q else (None, ())
def peek(q):
    return q[0] if q else None
queue = ()
queue = enqueue(queue, "Apple")
queue = enqueue(queue, "Banana")
queue = enqueue(queue, "Cherry")
print(queue)
print(peek(queue))
item, queue = dequeue(queue)
print(item, queue)
print(item, queue)
print(item, queue)
