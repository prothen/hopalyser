#!/usr/bin/env python
"""

Simple asyncio test script.

Author: Philipp Rothenhäusler, Smart Mobility Lab, KTH , Stockholm 2020

"""
import asyncio
import concurrent.futures

def test():
    print('test called.')

async def _sleep(sleep, ):
    print('{0:4.2f}: Received call. Wait {1}'.format(asyncio.get_event_loop().time(), sleep))
    await asyncio.sleep(sleep)
    print("{0:4.2f}: slept for {1} second.".format(asyncio.get_event_loop().time(), sleep))
    #asyncio.get_event_loop().call_soon(_sleep, 2)

async def loop(sleep):
    t1 = asyncio.create_task(_sleep(1))
    print('launched t1')
    await _sleep(2)
    print('done 2s')
    print('wait for t1')
    await t1
    print('waited for t1')
    print('-----------')

    t2 = asyncio.create_task(_sleep(2))
    t3 = asyncio.create_task(_sleep(3))
    #await asyncio.gather([t1,t2,t3])
    #l = asyncio.run_in_executor()
    await _sleep(5)
    print('done with callback stuff')
    asyncio.get_event_loop().stop()

    #await asyncio.gather([t1,t2,t3])
    l = asyncio.get_event_loop()
    f = l.create_future()
    print('schedule next callback')
    l.call_at(0,_sleep, 1, f)
    print('wait future')
    await f
    print('Stop loop.')
    asyncio.get_event_loop().stop()

async def loopmelongtime():
    while True:
        await _sleep(1)

def mp_loop(_corout, *args):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        asyncio.ensure_future(_corout(*args))
        return loop.run_forever()
    except Exception as e:
        print('lool error: \n{0}'.format(e))
    finally:
        loop.close()

async def jumpad():
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    #l = asyncio.get_event_loop()
    asyncio.get_event_loop().run_in_executor(ex, mp_loop,loopmelongtime)# _sleep, 1)
    #l.run_forever()

if __name__ == "__main__":
    print('Main called.')
    l = asyncio.get_event_loop()
    #asyncio.ensure_future(_sleep(1))
    #asyncio.ensure_future(loop(1))
    #asyncio.ensure_future(jumpad())
    l.run_until_complete(jumpad())
    print('Is it actually running unblocking??')
    import time as ti
    while True:
        print('Mainloop idleing around lol')
        ti.sleep(0.5)

