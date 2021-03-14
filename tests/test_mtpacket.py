import asyncio
import mtrpacket


async def ping_me():
    async with mtrpacket.MtrPacket() as mtr:
        print('pinging')
        res = await mtr.probe("localhost")
        print(res)
        print('pinging done.')
    asyncio.get_event_loop().stop()


async def trace_me(target):
    probes = []
    async with mtrpacket.MtrPacket() as mtr:
        async def probe_me(ttl):
            probe = await mtr.probe(target, protocol='udp',port=2000, ttl=ttl, timeout=1)
            #probes += probe.time_ms * 1.e3# todo: change probe here to ping result
            #print('Trace result for it: {0} with probe res:\n{1}'.format(ttl, probe.time_ms))
            #print('\n\n------')
            #print('IT:  \t{}'.format(ttl))
            #print(probe)
            #print('latency: \t{}us'.format(probe.time_ms*1.e3))
            #print('SRC: \t{}'.format(probe.responder))
            return (ttl,probe)
        T = [probe_me(i) for i in range(2, 20)]
        res = await asyncio.gather(*T)
        for i in range(2,20):
            print(res[i][1].time_ms)
            if res[i][1].result == 'no-reply':
                print(res[:i-1])
                return res[:i-1]
        print(res)

if __name__ == "__main__":
    print('start test')
    HOST = "34.199.231.194"
    l = asyncio.get_event_loop()
    #l.create_task(ping_me())
    l.create_task(trace_me(HOST))
    l.run_forever()
    print('executed')
