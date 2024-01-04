#!/usr/bin/env python

# _433.py
# 2015-10-30
# Public Domain

"""
This module provides two classes to use with wireless 433MHz/315MHz fobs.
The rx class decodes received fob codes. The tx class transmits
fob codes.
"""
import time
import pigpio
import threading


class rx():
    debounce = threading.Event()
    last_remote = None
    last_button = None

    """
   A class to read the wireless codes transmitted by 433 MHz
   wireless fobs.
   """

    def __init__(self, gpio, pi = None, callback=None,
                 min_bits=24, max_bits=24, glitch=150):
        """
        Instantiate with the Pi and the GPIO connected to the wireless
        receiver.

        If specified the callback will be called whenever a new code
        is received.  The callback will be passed the code, the number
        of bits, the length (in us) of the gap, short pulse, and long
        pulse.

        Codes with bit lengths outside the range min_bits to max_bits
        will be ignored.

        A glitch filter will be used to remove edges shorter than
        glitch us long from the wireless stream.  This is intended
        to remove the bulk of radio noise.
        """
        if pi is None:
            pi = pigpio.pi()

        self.pi = pi
        self.gpio = gpio
        self.cb = callback
        self.min_bits = min_bits
        self.max_bits = max_bits
        self.glitch = glitch

        self._in_code = False
        self._edge = 0
        self._code = 0
        self._gap = 0

        self._ready = False

        pi.set_mode(gpio, pigpio.INPUT)
        pi.set_glitch_filter(gpio, glitch)

        self._last_edge_tick = pi.get_current_tick()
        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

    def _timings(self, e0, e1):
        """
        Accumulates the short and long pulse length so that an
        average short/long pulse length can be calculated. The
        figures may be used to tune the transimission settings.
        """
        if e0 < e1:
            shorter = e0
            longer = e1
        else:
            shorter = e1
            longer = e0

        if self._bits:
            self._t0 += shorter
            self._t1 += longer
        else:
            self._t0 = shorter
            self._t1 = longer

        self._bits += 1

    def _calibrate(self, e0, e1):
        """
        The first pair of pulses is used as the template for
        subsequent pulses.  They should be one short, one long, not
        necessarily in that order.  The ratio between long and short
        should really be 2 or more.  If less than 1.5 the pulses are
        assumed to be noise.
        """
        self._bits = 0
        self._timings(e0, e1)
        self._bits = 0

        ratio = float(self._t1) / float(self._t0)

        if ratio < 1.5:
            self._in_code = False

        slack0 = int(0.3 * self._t0)
        slack1 = int(0.2 * self._t1)

        self._min_0 = self._t0 - slack0
        self._max_0 = self._t0 + slack0
        self._min_1 = self._t1 - slack1
        self._max_1 = self._t1 + slack1

    def _test_bit(self, e0, e1):
        """
        Returns the bit value represented by the sequence of pulses.

        0: short long
        1: long short
        2: illegal sequence
        """
        self._timings(e0, e1)

        if ((self._min_0 < e0 < self._max_0)
                and (self._min_1 < e1 < self._max_1)):
            return 0
        elif ((self._min_0 < e1 < self._max_0)
              and (self._min_1 < e0 < self._max_1)):
            return 1
        else:
            return 2

    def _cbf(self, g, l, t):
        """
        Accumulates the code from pairs of short/long pulses.
        The code end is assumed when an edge greater than 5 ms
        is detected.
        """
        edge_len = pigpio.tickDiff(self._last_edge_tick, t)
        self._last_edge_tick = t

        if edge_len > 5000:  # 5000 us, 5 ms.

            if self._in_code:
                if self.min_bits <= self._bits <= self.max_bits:
                    self._lbits = self._bits
                    self._lcode = self._code
                    self._lgap = self._gap
                    self._lt0 = int(self._t0 / self._bits)
                    self._lt1 = int(self._t1 / self._bits)
                    self._ready = True
                    if self.cb is not None:
                        # Break out the sending remote and the button pushed from the code received
                        remote_id = self._lcode >> 4

                        button = self._lcode & (0b1111)
                        button_mask = 1
                        button_num = 1
                        while not button & button_mask:
                            button_mask = button_mask << 1
                            button_num += 1

                        # Only process each unique button press once, even if the button is held down.
                        # Note that we are doing an up-front process, that is process as soon as
                        # the first event is received, and then ignore subsiqent identical events
                        # for a time. The time is short so it only applies if the button is held
                        # down, releasing and pushing the button again SHOULD trigger a new event
                        # process.
                        if remote_id == self.last_remote and \
                           button == self.last_button and \
                           self.debounce.is_set():
                            # We are bouncing. Try to reset the clear timer
                            try:
                                self.db_timer.cancel()
                            except AttributeError:
                                # No timer yet. No problem.
                                pass
                            self.db_timer = threading.Timer(.5, self.debounce.clear)
                            self.db_timer.start()
                        else:
                            self.last_button = button
                            self.last_remote = remote_id
                            self.debounce.set()  # Process in this call, other calls will skip

                            self.cb(remote_id, button_num, self._lcode, self._lbits,
                                    self._lgap, self._lt0, self._lt1)

            self._in_code = True
            self._gap = edge_len
            self._edge = 0
            self._bits = 0
            self._code = 0

        elif self._in_code:

            if self._edge == 0:
                self._e0 = edge_len
            elif self._edge == 1:
                self._calibrate(self._e0, edge_len)

            if self._edge % 2:  # Odd edge.

                bit = self._test_bit(self._even_edge_len, edge_len)
                self._code = self._code << 1
                if bit == 1:
                    self._code += 1
                elif bit != 0:
                    self._in_code = False

            else:  # Even edge.

                self._even_edge_len = edge_len

            self._edge += 1

    def ready(self):
        """
        Returns True if a new code is ready.
        """
        return self._ready

    def code(self):
        """
        Returns the last receieved code.
        """
        self._ready = False
        return self._lcode

    def details(self):
        """
        Returns details of the last receieved code.  The details
        consist of the code, the number of bits, the length (in us)
        of the gap, short pulse, and long pulse.
        """
        self._ready = False
        return self._lcode, self._lbits, self._lgap, self._lt0, self._lt1

    def cancel(self):
        """
        Cancels the wireless code receiver.
        """
        if self._cb is not None:
            self.pi.set_glitch_filter(self.gpio, 0)  # Remove glitch filter.
            self._cb.cancel()
            self._cb = None


if __name__ == "__main__":
    import pigpio
    from signal import pause

    RX = 20
    # define optional callback for received codes.

    def rx_callback(remote_id, button_num, code, bits, gap, t0, t1):
        print(f"Remote ID: {remote_id} Button: {button_num} Bits: {bits} gap: {gap} t0:{t0} t1:{t1}")

    pi = pigpio.pi()  # Connect to local Pi.

    rx = rx(pi, gpio=RX, callback=rx_callback, min_bits=24, max_bits=24, glitch=250)

    print(f"Waiting for input on GPIO {RX}")
    pause()
