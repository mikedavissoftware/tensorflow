# Copyright 2020 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for script operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorflow.python.eager import def_function
from tensorflow.python.framework import dtypes
from tensorflow.python.framework import test_util
from tensorflow.python.framework import constant_op
from tensorflow.python.ops import script_ops
from tensorflow.python.ops.script_ops import numpy_function
from tensorflow.python.ops.variables import Variable
from tensorflow.python.platform import test


class NumpyFunctionTest(test.TestCase):

  @test_util.run_in_graph_and_eager_modes
  def test_numpy_arguments(self):

    def plus(a, b):
      return a + b

    actual_result = script_ops.numpy_function(plus, [1, 2], dtypes.int32)
    expect_result = constant_op.constant(3, dtypes.int32)
    self.assertAllEqual(actual_result, expect_result)

  def test_stateless_flag(self):
    call_count = Variable(0, dtype=dtypes.int32)

    # make sure to have a significant difference to the expected number of execution, which is 1
    nruns = 10

    def plus(a, b):
      call_count.assign_add(1)
      return a + b

    @def_function.function
    def tensor_double_plus_stateless(a, b):
      sum1 = 0.
      for _ in range(nruns):
        sum1 += numpy_function(plus, [a, b], dtypes.int32, stateful=False)
      return sum1

    # different argument
    tensor_double_plus_stateless(
      constant_op.constant(1),
      constant_op.constant(2),
    )
    # This is not a safe test: as the docs say, using a stateful function while guaranteeing statelessness is
    # undefined. Since it is a guarantee we give without receiving anything for it, we cannot test an expected
    # behavior really. As a proxy, we can say that it will *most likely* not be called 10 times.
    self.assertNotEqual(call_count, nruns)  # If it is 10, every call was executed (most likely)

    @def_function.function
    def tensor_double_plus_stateful(a, b):
      sum1 = 0.
      for _ in range(nruns):
        sum1 += numpy_function(plus, [a, b], dtypes.int32, stateful=True)
      return sum1

    call_count.assign(0)
    tensor_double_plus_stateful(
      constant_op.constant(3),
      constant_op.constant(4),
                          )
    self.assertEqual(call_count, nruns)  # as it is stateful, func was executed every time executed


if __name__ == "__main__":
  test.main()
