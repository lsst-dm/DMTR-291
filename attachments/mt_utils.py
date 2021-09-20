from astropy.coordinates import AltAz, ICRS, EarthLocation, Angle
from astropy.time import Time
import astropy.units as u

from lsst.ts.idl.enums import MTM1M3
from lsst.ts.observatory.control.utils import RotType
from lsst.ts import salobj

def altaz_to_radec(alt, az):
    location = EarthLocation.from_geodetic(
        lon=-70.747698 * u.deg, lat=-30.244728 * u.deg, height=2663.0 * u.m
    )

    current_time = salobj.astropy_time_from_tai_unix(salobj.current_tai())
    current_time.location = location

    coord_frame_radec = ICRS()

    alt_az = AltAz(
        az=Angle(az, unit=u.deg),
        alt=Angle(alt, unit=u.deg),
        location=location,
        obstime=current_time
    )

    return alt_az.transform_to(coord_frame_radec)

async def slew_to_park(mtcs, rotpa=0.0):
    ra_dec = altaz_to_radec(80.0, 0.0)

    await mtcs.slew_icrs(ra=ra_dec.ra.hour,
                         dec=ra_dec.dec.deg,
                         rot=Angle(rotpa, unit=u.deg).deg,
                         rot_type=RotType.PhysicalSky,
                         target_name="Park position")
    await stop_mt_tracking(mtcs)

async def slew_to_flatfield(mtcs, rotpa=0.0):
    ra_dec = altaz_to_radec(39.0, 205.7)

    await mtcs.slew_icrs(ra=ra_dec.ra.hour,
                         dec=ra_dec.dec.deg,
                         rot=Angle(rotpa, unit=u.deg).deg,
                         rot_type=RotType.PhysicalSky,
                         target_name="Flatfield position")
    await stop_mt_tracking(mtcs)

async def slew_to_target(mtcs, target_name, ra, dec, rotpa):
    radec_icrs = ICRS(Angle(ra, unit=u.hourangle), Angle(dec, unit=u.deg))

    await mtcs.slew_icrs(ra=radec_icrs.ra.hour,
                         dec=radec_icrs.dec.deg,
                         rot=Angle(rotpa, unit=u.deg).deg,
                         rot_type=RotType.PhysicalSky,
                         target_name=target_name)

async def slew_to_altaz(mtcs, alt, az, rotpa=0.0):
    ra_dec = altaz_to_radec(alt, az)

    await mtcs.slew_icrs(ra=ra_dec.ra.hour,
                         dec=ra_dec.dec.deg,
                         rot=Angle(rotpa, unit=u.deg).deg,
                         rot_type=RotType.PhysicalSky,
                         target_name="AltAz position")    

async def stop_mt_tracking(mtcs):
    ack = await mtcs.rem.mtptg.cmd_stopTracking.start(timeout=30.)
    print("Stop Tracking")
    print(f"ack={ack.ack} ack.error={ack.error}, ackcmd.result={ack.result}")

async def slew2(mtcs, stop_tracking=False):
    print("Slewing Telescope")
    ack = await mtcs.rem.mtptg.cmd_raDecTarget.start(timeout=30.)
    print(f"ack={ack.ack} ack.error={ack.error}, ackcmd.result={ack.result}")
    result = await mtcs.wait_in_position(30.)
    print(result)

    if stop_tracking:
        await stop_mt_tracking(mtcs)

async def slew(mtcs, stop_tracking=False):
    print("Slewing Telescope")
    ack = await mtcs.rem.mtptg.cmd_raDecTarget.start(timeout=30.)
    print(f"ack={ack.ack} ack.error={ack.error}, ackcmd.result={ack.result}")
    while True:
        in_position = await mtcs.rem.newmtmount.evt_axesInPosition.next(flush=False, timeout=60.)
        print(f"State: {in_position.elevation}, {in_position.azimuth}")
        if in_position.elevation and in_position.azimuth:
            print("Telescope in position.")
            break

    if stop_tracking:
        await stop_mt_tracking(mtcs)


async def lower_M1M3_mirror(mtcs):
    m1m3 = mtcs.rem.mtm1m3
    m1m3.evt_detailedState.flush()
    await m1m3.cmd_lowerM1M3.set_start(lowerM1M3=True, timeout = 30)
    while True:
        state = await m1m3.evt_detailedState.next(flush=False, timeout=300)
        print(MTM1M3.DetailedState(state.detailedState))
        if (MTM1M3.DetailedState(state.detailedState) == MTM1M3.DetailedState.PARKED
                or MTM1M3.DetailedState(state.detailedState) == MTM1M3.DetailedState.PARKEDENGINEERING):
            break
            
async def raise_M1M3_mirror(mtcs):
    m1m3 = mtcs.rem.mtm1m3
    m1m3.evt_detailedState.flush()
    await m1m3.cmd_raiseM1M3.set_start(raiseM1M3=True, timeout = 30)
    while True:
        state = await m1m3.evt_detailedState.next(flush=False, timeout=300)
        print(MTM1M3.DetailedState(state.detailedState))
        if (MTM1M3.DetailedState(state.detailedState) == MTM1M3.DetailedState.ACTIVE
                or MTM1M3.DetailedState(state.detailedState) == MTM1M3.DetailedState.ACTIVEENGINEERING):
            break