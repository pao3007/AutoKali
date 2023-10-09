class ThreadControlFuncGenStatements:
    def __init__(self):
        self._start_sens_test = False
        self._end_sens_test = False
        self._start_measuring = False
        self._finished_measuring = False
        self._emergency_stop = False
        self._sentinel_started = False
        self.termination = False

    def get_termination(self):
        return self.termination

    def set_termination(self, value):
        self.termination = value

    def get_start_sens_test(self):
        return self._start_sens_test

    def set_start_sens_test(self, value):
        self._start_sens_test = value

    def get_end_sens_test(self):
        return self._end_sens_test

    def set_end_sens_test(self, value):
        self._end_sens_test = value

    def get_start_measuring(self):
        return self._start_measuring

    def set_start_measuring(self, value):
        self._start_measuring = value

    def get_finished_measuring(self):
        return self._finished_measuring

    def set_finished_measuring(self, value):
        self._finished_measuring = value

    def get_emergency_stop(self):
        return self._emergency_stop

    def set_emergency_stop(self, value):
        self._emergency_stop = value

    def get_sentinel_started(self):
        return self._sentinel_started

    def set_sentinel_started(self, value):
        self._sentinel_started = value
