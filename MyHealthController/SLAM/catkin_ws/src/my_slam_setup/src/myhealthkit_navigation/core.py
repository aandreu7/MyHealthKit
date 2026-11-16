"""Geometry and guards, independent of ROS and GPIO (Python 3.8 compatible)."""
import math


def angle_delta(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


class PoseVelocity:
    def __init__(self, max_linear=0.6, max_angular=1.5, max_gap=0.5, tau=0.15):
        if not all(math.isfinite(v) and v > 0 for v in (max_linear, max_angular, max_gap)) or not math.isfinite(tau) or tau < 0:
            raise ValueError('Invalid velocity estimator configuration')
        self.max_linear, self.max_angular = max_linear, max_angular
        self.max_gap, self.tau = max_gap, tau
        self.previous = None
        self.velocity = (0.0, 0.0, 0.0)

    def update(self, stamp, x, y, yaw):
        """Body-frame velocity, or None for first/gap/out-of-order samples.

        Implausible jumps raise ValueError; the ROS node latches a fault.
        """
        if not all(math.isfinite(v) for v in (stamp, x, y, yaw)):
            raise ValueError('Non-finite pose')
        sample = (stamp, x, y, yaw)
        if self.previous is None:
            self.previous = sample
            return None
        t0, x0, y0, yaw0 = self.previous
        dt = stamp - t0
        if dt <= 0:
            return None
        dx, dy, dyaw = x - x0, y - y0, angle_delta(yaw, yaw0)
        if math.hypot(dx, dy) > self.max_linear * dt + 0.05 or abs(dyaw) > self.max_angular * dt + 0.05:
            raise ValueError('LiDAR pose jump exceeds motion limits')
        self.previous = sample
        if dt > self.max_gap:
            self.velocity = (0.0, 0.0, 0.0)
            return None
        mid = yaw0 + dyaw / 2.0
        raw = ((math.cos(mid)*dx + math.sin(mid)*dy)/dt,
               (-math.sin(mid)*dx + math.cos(mid)*dy)/dt, dyaw/dt)
        alpha = dt / (self.tau + dt)
        self.velocity = tuple(old + alpha*(new-old) for old, new in zip(self.velocity, raw))
        return self.velocity


def wheel_duties(linear, angular, wheel_base, speed_at_full_duty):
    if not all(math.isfinite(v) for v in (linear, angular, wheel_base, speed_at_full_duty)):
        raise ValueError('Non-finite motor command')
    if wheel_base <= 0 or speed_at_full_duty <= 0:
        raise ValueError('Motor calibration must be positive')
    left = (linear - angular * wheel_base / 2.0) / speed_at_full_duty
    right = (linear + angular * wheel_base / 2.0) / speed_at_full_duty
    scale = max(1.0, abs(left), abs(right))
    return left / scale, right / scale


def validate_point(point):
    values = [float(point.get(k, default)) for k, default in
              [('x', None), ('y', None), ('z', 0), ('qx', 0), ('qy', 0), ('qz', 0), ('qw', 1)]]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Non-finite goal')
    x, y, z, qx, qy, qz, qw = values
    if abs(z) > 0.001 or abs(qx) > 0.001 or abs(qy) > 0.001:
        raise ValueError('Only planar map goals are supported')
    norm = math.hypot(qz, qw)
    if norm < 1e-6:
        raise ValueError('Zero goal quaternion')
    return x, y, qz/norm, qw/norm
