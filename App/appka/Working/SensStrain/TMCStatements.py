class TMCStatements:

    def __init__(self):
        print("INIT TMCS")
        self._start = False
        self._finished = False
        self._continue = False
        self._in_position = False
        self._home = False
        self._home_finished = False
        self._emergency_stop = False
        self._step = 0
        self._init_done = False
        self._termination = False
        self._inc = 0
        self._pos = []
        self._init_home = False
        self._init_exit = False
        self._init_home_finished = False
        self._init_exit_finished = False
        self._output_bench = []
        self._move_to_action = False
        self._move_to_action_finished = False
        self._move_by_action = False
        self._move_by_action_finished = False
        self._move_to_position = 0.0
        self._move_by_length = 0.0
        self._move_by_direction = -1
        self._current_position = 0.0
        self._termination_pos = False
        self._opt_wls = []
        self._ref_pos = []
        self._error = False

        self._disable_usb_check = False

    @property
    def ref_pos(self):
        return self._ref_pos

    @ref_pos.setter
    def ref_pos(self, value):
        if all(isinstance(item, float) for item in value) and isinstance(value, list):
            self._ref_pos = value
        else:
            raise ValueError("ref_pos must be a list of float values.")

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        if isinstance(value, bool):
            self._error = value
        else:
            raise ValueError("The error attribute must be set to a boolean value.")

    @property
    def termination_pos(self):
        return self._termination_pos

    @termination_pos.setter
    def termination_pos(self, value):
        if isinstance(value, bool):
            self._termination_pos = value
        else:
            raise ValueError("termination_pos must be a boolean value")

    @property
    def disable_usb_check(self):
        return self._disable_usb_check

    @disable_usb_check.setter
    def disable_usb_check(self, value):
        if isinstance(value, bool):
            self._disable_usb_check = value
        else:
            raise ValueError("disable_usb_check must be a boolean value")

    @property
    def opt_wls(self):
        return self._opt_wls

    @opt_wls.setter
    def opt_wls(self, value):
        if isinstance(value, list):
            self._opt_wls = value
        else:
            raise ValueError("opt_wls must be a list")

    @property
    def current_position(self):
        return self._current_position

    @current_position.setter
    def current_position(self, value):
        if isinstance(value, (int, float)):
            self._current_position = float(value)
        else:
            raise ValueError("Current Position value must be an int or float.")

    @property
    def move_by_direction(self):
        return self._move_by_direction

    @move_by_direction.setter
    def move_by_direction(self, value):
        if value in [1, -1]:
            self._move_by_direction = value
        else:
            raise ValueError("Move By Direction value must be either 1 or -1.")

    @property
    def move_to_position(self):
        return self._move_to_position

    @move_to_position.setter
    def move_to_position(self, value):
        if isinstance(value, (int, float)):
            self._move_to_position = value
        else:
            raise ValueError("Move To Position value must be an int or float.")

    @property
    def move_by_length(self):
        return self._move_by_length

    @move_by_length.setter
    def move_by_length(self, value):
        if isinstance(value, (int, float)):
            self._move_by_length = value
        else:
            raise ValueError("Move By Length value must be an int or float.")

    @property
    def move_to_action(self):
        return self._move_to_action

    @move_to_action.setter
    def move_to_action(self, value):
        if isinstance(value, bool):
            self._move_to_action = value
        else:
            raise ValueError("Move To Action value must be a boolean.")

    @property
    def move_to_action_finished(self):
        return self._move_to_action_finished

    @move_to_action_finished.setter
    def move_to_action_finished(self, value):
        if isinstance(value, bool):
            self._move_to_action_finished = value
        else:
            raise ValueError("Move To Action Finished value must be a boolean.")

    @property
    def move_by_action(self):
        return self._move_by_action

    @move_by_action.setter
    def move_by_action(self, value):
        if isinstance(value, bool):
            self._move_by_action = value
        else:
            raise ValueError("Move By Action value must be a boolean.")

    @property
    def move_by_action_finished(self):
        return self._move_by_action_finished

    @move_by_action_finished.setter
    def move_by_action_finished(self, value):
        if isinstance(value, bool):
            self._move_by_action_finished = value
        else:
            raise ValueError("Move By Action Finished value must be a boolean.")

    @property
    def init_home(self):
        return self._init_home

    @init_home.setter
    def init_home(self, value):
        if isinstance(value, bool):
            self._init_home = value
        else:
            raise ValueError("Init Home value must be a boolean.")

    @property
    def init_exit(self):
        return self._init_exit

    @init_exit.setter
    def init_exit(self, value):
        if isinstance(value, bool):
            self._init_exit = value
        else:
            raise ValueError("Init Exit value must be a boolean.")

    @property
    def termination(self):
        return self._termination

    @termination.setter
    def termination(self, value):
        if isinstance(value, bool):
            self._termination = value
        else:
            raise ValueError("Termination value must be a boolean.")

    @property
    def init_done(self):
        return self._init_done

    @init_done.setter
    def init_done(self, value):
        if isinstance(value, bool):
            self._init_done = value
        else:
            raise ValueError("Init Done value must be a boolean.")

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        if isinstance(value, int):
            self._step = value
        else:
            raise ValueError("Step value must be an integer.")

    @property
    def emergency_stop(self):
        return self._emergency_stop

    @emergency_stop.setter
    def emergency_stop(self, value):
        if isinstance(value, bool):
            self._emergency_stop = value
        else:
            raise ValueError("Emergency Stop value must be a boolean.")

    @property
    def home_finished(self):
        return self._home_finished

    @home_finished.setter
    def home_finished(self, value):
        if isinstance(value, bool):
            self._home_finished = value
        else:
            raise ValueError("Home Finished value must be a boolean.")

    @property
    def home(self):
        return self._home

    @home.setter
    def home(self, value):
        if isinstance(value, bool):
            self._home = value
        else:
            raise ValueError("Home value must be a boolean.")

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        if isinstance(value, bool):
            self._start = value
        else:
            raise ValueError("Start value must be a boolean.")

    @property
    def finished(self):
        return self._finished

    @finished.setter
    def finished(self, value):
        if isinstance(value, bool):
            self._finished = value
        else:
            raise ValueError("Finished value must be a boolean.")

    @property
    def continue_flag(self):
        return self._continue

    @continue_flag.setter
    def continue_flag(self, value):
        if isinstance(value, bool):
            self._continue = value
        else:
            raise ValueError("Continue value must be a boolean.")

    @property
    def in_position(self):
        return self._in_position

    @in_position.setter
    def in_position(self, value):
        if isinstance(value, bool):
            self._in_position = value
        else:
            raise ValueError("In Position value must be a boolean.")

    @property
    def inc(self):
        return self._inc

    @inc.setter
    def inc(self, value):
        if isinstance(value, (int, float)):
            self._inc = value
        else:
            raise ValueError("Inc value must be an integer.")

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        if isinstance(value, list) and all(isinstance(x, float) for x in value):
            self._pos = value
        else:
            raise ValueError("Pos value must be a list of floats.")

    @property
    def init_home_finished(self):
        return self._init_home_finished

    @init_home_finished.setter
    def init_home_finished(self, value):
        if isinstance(value, bool):
            self._init_home_finished = value
        else:
            raise ValueError("Init Home Finished value must be a boolean.")

    @property
    def init_exit_finished(self):
        return self._init_exit_finished

    @init_exit_finished.setter
    def init_exit_finished(self, value):
        if isinstance(value, bool):
            self._init_exit_finished = value
        else:
            raise ValueError("Init Exit Finished value must be a boolean.")

    @property
    def output_bench(self):
        return self._output_bench

    @output_bench.setter
    def output_bench(self, value):
        if isinstance(value, list) and all(isinstance(x, float) for x in value):
            self._output_bench = value
        else:
            raise ValueError("Output Bench value must be a list of floats.")

    def reset(self):
        self._start = False
        self._finished = False
        self._continue = False
        self._in_position = False
        self._home = False
        self._home_finished = False
        self._emergency_stop = False
        self._step = 0
        self._termination = False
        self._pos = []
        self._init_home = False
        self._init_exit = False
        self._init_home_finished = False
        self._init_exit_finished = False
