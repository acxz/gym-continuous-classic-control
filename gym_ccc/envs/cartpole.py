"""Continuous CartPole Environment."""
from gym import spaces
from gym.envs import classic_control

import numpy as np


# pylint: disable=too-many-instance-attributes
class CartPoleNonNormEnv(classic_control.CartPoleEnv):
    """
    Continuous cartpole that outputs the state as the observation.

    Description:
        A pole is attached by an un-actuated joint to a cart, which moves along
        a frictionless track. The pendulum starts upright, and the goal is to
        prevent it from falling over by increasing and reducing the cart's
        velocity.
    Observation:
        Type: Box(4)
        Num     Observation               Min                     Max
        0       Cart Position             -Inf                    Inf
        1       Cart Velocity             -Inf                    Inf
        2       Pole Angle                -Pi rad                 Pi rad
        3       Pole Angular Velocity     -Inf                    Inf
    Actions:
        Type: Box(1)
        Num   Action                      Min                     Max
        0     Force on the cart           -Inf                    Inf
    Reward:
        Quadratic cost from goal state of [0, 0, 0, 0]
    Starting State:
        All observations are assigned a uniform random value in [-0.05..0.05]
    """

    # pylint: disable=too-many-arguments
    def __init__(self, gravity=9.8, masscart=1.0, masspole=0.1, polelength=1.0,
                 dt=0.02, custom_reset=None):
        """Init cartpole env."""
        super().__init__()

        self.gravity = gravity
        self.masscart = masscart
        self.masspole = masspole
        self.polelength = polelength
        self.length = self.polelength/2  # For rendering purposes
        # pylint: disable=invalid-name
        self.dt = dt

        self.state = None
        self.time = 0

        self.custom_reset = custom_reset

        action_high = np.array([np.finfo(np.float32).max], dtype=np.float32)

        obs_high = np.array([np.finfo(np.float32).max,
                             np.finfo(np.float32).max,
                             np.pi,
                             np.finfo(np.float32).max],
                            dtype=np.float32)

        self.action_space = spaces.Box(-action_high,
                                       action_high, dtype=np.float32)
        self.observation_space = spaces.Box(-obs_high,
                                            obs_high, dtype=np.float32)

    def step(self, action):
        """Propagate dynamics."""
        pos, pos_dot, theta, theta_dot = self.state
        force = action
        self.time += self.dt

        cost = pos ** 2 + pos_dot ** 2 + theta ** 2 + theta_dot ** 2

        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        temp = self.masscart + self.masspole * sintheta ** 2
        pos_acc = 1/temp * (self.masspole * sintheta *
                            (self.polelength * theta_dot**2 +
                             self.gravity * costheta)
                            + force)

        theta_acc = (1/(self.polelength * temp) *
                     (- self.masspole * self.polelength * theta_dot**2 *
                      costheta * sintheta -
                     (self.masscart + self.masspole) * self.gravity *
                     sintheta -
                     force * costheta))

        pos = pos + self.dt * pos_dot
        pos_dot = pos_dot + self.dt * pos_acc
        theta = theta + self.dt * theta_dot
        theta_dot = theta_dot + self.dt * theta_acc

        theta = self.angle_normalize(theta)
        self.state = np.array([pos, pos_dot, theta, theta_dot],
                              dtype=np.float32)

        return self.state, -cost, False, {'time': self.time}

    def reset(self):
        """Reset environment."""
        self.time = 0
        if self.custom_reset is not None:
            self.state = self.custom_reset()
        else:
            self.state = \
                self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        return self.state

    @staticmethod
    def angle_normalize(ang):
        """Normalize angle between -pi and pi."""
        return ((ang+np.pi) % (2*np.pi)) - np.pi


class CartPoleEnv(CartPoleNonNormEnv):
    """Continuous cartpole with normalized observation and state in info."""

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(**kwargs)

        obs_high = np.array([np.finfo(np.float32).max,
                             np.finfo(np.float32).max,
                             1,
                             1,
                             np.finfo(np.float32).max],
                            dtype=np.float32)

        self.observation_space = spaces.Box(-obs_high,
                                            obs_high, dtype=np.float32)

    def step(self, action):
        """Propagate dynamics forward and keep track of state in info."""
        _, reward, done, info = super().step(action)
        info['state'] = self.state

        return self._get_obs(), reward, done, info

    def reset(self):
        """Reset to a random observation."""
        self.state = super().reset()
        return self._get_obs()

    def _get_obs(self):
        pos, pos_dot, theta, theta_dot = self.state
        return np.array([pos, pos_dot, np.cos(theta), np.sin(theta),
                         theta_dot])
