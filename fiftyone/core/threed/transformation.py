from typing import List, Literal, Tuple, Union

import numpy as np
from pydantic.dataclasses import dataclass
from scipy.spatial.transform import Rotation


@dataclass(frozen=True)
class Vector3:
    """Represents a three-dimensional vector."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_arr(self):
        """Converts the vector to a numpy array."""
        return np.array([self.x, self.y, self.z])


@dataclass(frozen=True)
class Euler:
    """Represents intrinsic rotations about the object's own principal axes."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    degrees: bool = False
    sequence: Literal["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"] = "XYZ"

    def to_quaternion(self):
        """Converts the euler angles to a quaternion."""
        q = Rotation.from_euler(
            self.sequence, [self.x, self.y, self.z], degrees=self.degrees
        )
        return Quaternion(*q.as_quat())

    def to_arr(self):
        """Converts the euler angles to a numpy array."""
        return np.array([self.x, self.y, self.z])


@dataclass(frozen=True)
class Quaternion:
    """Represents a quaternion."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0

    def to_euler(self, degrees=False, sequence="XYZ"):
        """Converts the quaternion into euler angles."""
        q = Rotation.from_quat([self.x, self.y, self.z, self.w])
        return Euler(*q.as_euler(sequence, degrees=degrees))

    def to_arr(self):
        """Converts the quaternion to a numpy array."""
        return np.array([self.x, self.y, self.z, self.w])


Vec3UnionType = Union[Vector3, List[float], Tuple[float]]
