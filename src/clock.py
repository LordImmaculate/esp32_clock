import os
import time
import ntptime  # type: ignore
from machine import Pin, SoftI2C  # type: ignore
from machine_i2c_lcd import I2cLcd  # type: ignore
import _thread
import globals


def is_dst_active(t):
    # Determine if Daylight Saving Time (DST) is active based on the given time tuple.
    year, month, day, hour, _, _, weekday, _ = t

    # 1. DST Starts: Last Sunday in March
    if month == 3:
        # Find the day of the last Sunday in March
        # March has 31 days. Start looking from day 31 back.
        last_sunday = 31
        while (
            time.localtime(time.mktime((year, 3, last_sunday, 2, 0, 0, 0, 0)))[6] != 6
        ):  # weekday 6 is Sunday
            last_sunday -= 1

        if day > last_sunday:
            return True
        elif day == last_sunday and hour >= 2:
            return True

    # 2. DST Active: April through September
    if 4 <= month <= 9:
        return True

    # 3. DST Ends: Last Sunday in October
    if month == 10:
        # Find the day of the last Sunday in October
        # October has 31 days. Start looking from day 31 back.
        last_sunday = 31
        while (
            time.localtime(time.mktime((year, 10, last_sunday, 3, 0, 0, 0, 0)))[6] != 6
        ):  # weekday 6 is Sunday
            last_sunday -= 1

        if day < last_sunday:
            return True
        elif day == last_sunday and hour < 3:
            return True

    # 4. Winter Time (Nov, Dec, Jan, Feb) or before March/after October DST change
    return False


def get_current_offset_seconds(t_utc):
    if is_dst_active(t_utc):
        return globals.SETTINGS["summer"] * 3600
    else:
        return globals.SETTINGS["winter"] * 3600


def get_formatted_time(first_run):
    """
    Retrieves the time, calculates the local time (CET/CEST)
    and returns a formatted string.
    """

    if first_run:
        try:
            print("Syncing time with NTP...")
            ntptime.settime()  # Sync time with NTP server
            print("Time synchronized.")
        except Exception as e:
            print("Failed to sync time:", e)
            globals.LCD_MESSAGE = "Time sync error"
            return "Time sync error"

    # 1. Get current time tuple in UTC
    t_utc = time.localtime()

    # 2. Determine the correct offset (handles DST)
    offset_seconds = get_current_offset_seconds(t_utc)

    # 3. Convert UTC tuple to seconds since epoch (2000-01-01)
    utc_time_s = time.mktime(t_utc)

    # 4. Apply the offset
    local_time_s = utc_time_s + offset_seconds

    # 5. Convert the adjusted seconds back to a local time tuple
    t_local = time.localtime(local_time_s)

    formatted_time = "{:02}:{:02}     {:02}-{:02}-{:04}".format(
        t_local[3], t_local[4], t_local[2], t_local[1], t_local[0]
    )
    return [formatted_time, t_local]


def clock_task():
    I2C_ADDR = 0x27
    I2C_NUM_ROWS = 4
    I2C_NUM_COLS = 20

    i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
    lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

    first_run = True

    backlight_on_time = 0
    backlight_timeout = 999  # seconds
    alarm_triggered = False
    previous_time = None
    previous_alarm = globals.SETTINGS["alarm_hour"]

    while True:
        time.sleep(1)
        current_time = get_formatted_time(first_run)

        if (
            current_time[1][3] == globals.SETTINGS["alarm_hour"][0]
            and current_time[1][4] == globals.SETTINGS["alarm_hour"][1]
        ):
            if not alarm_triggered:
                backlight_on_time = time.time()
                lcd.backlight_on()
                alarm_triggered = True

        if alarm_triggered:
            if lcd.backlight:
                lcd.backlight_off()
            else:
                lcd.backlight_on()

        if globals.LCD_MESSAGE is not None:
            lcd.clear()
            lcd.putstr(globals.LCD_MESSAGE)
        elif (
            current_time[0] != previous_time
            or globals.SETTINGS["alarm_hour"] != previous_alarm
        ):
            previous_time = current_time[0]
            previous_alarm = globals.SETTINGS["alarm_hour"]
            lcd.clear()
            lcd.putstr(current_time[0])
            lcd.move_to(0, 1)
            lcd.putstr(
                "Alarm: {:02}:{:02}".format(
                    globals.SETTINGS["alarm_hour"][0], globals.SETTINGS["alarm_hour"][1]
                )
            )
            if first_run:
                backlight_on_time = time.time()
                lcd.backlight_on()
                first_run = False

        if (
            time.time() - backlight_on_time
        ) > backlight_timeout and not alarm_triggered:
            lcd.backlight_off()
