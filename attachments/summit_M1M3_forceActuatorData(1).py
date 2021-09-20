import asyncio
import datetime
import numpy as np
import time
from lsst_efd_client import EfdClient


async def main():
    efd_summit = EfdClient('summit_efd')

    cl = efd_summit.influx_client
    n_batch = 100
    sleep_time = 2.0

    with open('summit_M1M3_forceActuatorData.log', 'a') as fh:
        l_summit_datetime = []
        now_list_datetime = []
        then_list_datetime = []
#        fh.write('# now_before_query, now_after_query, private_sndStamp, private_seqNum, '
#                 'private_kafkaStamp, private_rcvStamp\n')
        while True:
            now_list_datetime.append(datetime.datetime.utcnow().timestamp())
            query_str = ('SELECT "private_seqNum", "private_rcvStamp", '
                         '"private_sndStamp", "private_kafkaStamp" FROM '
                         '"efd"."autogen"."lsst.sal.MTM1M3.forceActuatorData" WHERE time > now() - 2m')
            res_datetime = await cl.query(query_str)
            then_list_datetime.append(datetime.datetime.utcnow().timestamp())
            if len(res_datetime) == 0:
                l_summit_datetime.append((np.nan, np.nan, np.nan, np.nan))
            else:
                l_summit_datetime.append((res_datetime['private_sndStamp'][-1], res_datetime['private_seqNum'][-1],
                                          res_datetime['private_kafkaStamp'][-1], res_datetime['private_rcvStamp'][-1]))
            if not len(l_summit_datetime) % n_batch:
                for i in range(n_batch):
                    tstr = ", ".join([str(el) for el in l_summit_datetime[i]])
                    n = now_list_datetime[i]
                    t = then_list_datetime[i]
                    fh.write(f'{n}, {t}, {tstr}\n')
                l_summit_datetime = []
                now_list_datetime = []
                then_list_datetime = []
                fh.flush()
            time.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(main())
