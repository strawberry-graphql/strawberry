Release type: minor

Improve the time complexity of `strawberry.interface` using `resolve_type`.
Achieved time complexity is now O(1) with respect to the number of
implementations of an interface. Previously, the use of `is_type_of` resulted
in a worst-case performance of O(n).

**Before**:

```shell
---------------------------------------------------------------------------
Name (time in ms)                         Min                 Max
---------------------------------------------------------------------------
test_interface_performance[1]         18.0224 (1.0)       50.3003 (1.77)
test_interface_performance[16]        22.0060 (1.22)      28.4240 (1.0)
test_interface_performance[256]       69.1364 (3.84)      76.1349 (2.68)
test_interface_performance[4096]     219.6461 (12.19)    231.3732 (8.14)
---------------------------------------------------------------------------
```

**After**:

```shell
---------------------------------------------------------------------------
Name (time in ms)                        Min                Max
---------------------------------------------------------------------------
test_interface_performance[1]        14.3921 (1.0)      46.2064 (2.79)
test_interface_performance[16]       14.8669 (1.03)     16.5732 (1.0)
test_interface_performance[256]      15.8977 (1.10)     24.4618 (1.48)
test_interface_performance[4096]     18.7340 (1.30)     21.2899 (1.28)
---------------------------------------------------------------------------
```
