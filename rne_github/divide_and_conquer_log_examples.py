"""
Illustrative scripts that highlight logarithmic behavior in divide-and-conquer algorithms.

- binary_search_depth: shows how the number of comparisons grows with log2(n)
- merge_sort: demonstrates the recurrence T(n) = 2T(n/2) + O(n)
- build_segment_tree: constructs a tree-based index whose height stays logarithmic
"""

from __future__ import annotations

from bisect import bisect_left
from math import log2
from typing import List, Sequence, Tuple


def binary_search_depth(sorted_data: Sequence[int], target: int) -> Tuple[int, bool]:
    """
    Runs binary search and returns the number of iterations along with success flag.
    The iteration count should be close to ceil(log2(len(sorted_data))) when target exists.
    """
    low, high = 0, len(sorted_data) - 1
    steps = 0

    while low <= high:
        steps += 1
        mid = (low + high) // 2
        if sorted_data[mid] == target:
            return steps, True
        if sorted_data[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return steps, False


def merge_sort(data: List[int]) -> List[int]:
    """
    Classic divide-and-conquer sort. Each level of recursion splits the input in half, so the depth
    of recursion is logarithmic while the work per level sums to O(n).
    """
    if len(data) <= 1:
        return data

    mid = len(data) // 2
    left = merge_sort(data[:mid])
    right = merge_sort(data[mid:])
    return merge(left, right)


def merge(left: Sequence[int], right: Sequence[int]) -> List[int]:
    merged: List[int] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def build_segment_tree(data: Sequence[int]) -> List[int]:
    """
    Builds a segment tree (power-of-two sized array) to support logarithmic-range queries.
    """
    n = len(data)
    size = 1
    while size < n:
        size <<= 1
    tree = [0] * (2 * size)
    tree[size : size + n] = data
    for idx in range(size - 1, 0, -1):
        tree[idx] = tree[2 * idx] + tree[2 * idx + 1]
    return tree


def range_sum(tree: Sequence[int], n: int, left: int, right: int) -> int:
    """
    Computes the sum of data[left:right] using the tree in O(log n) time.
    """
    left += n
    right += n
    total = 0
    while left < right:
        if left & 1:
            total += tree[left]
            left += 1
        if right & 1:
            right -= 1
            total += tree[right]
        left //= 2
        right //= 2
    return total


if __name__ == "__main__":
    sample_sizes = [2**k for k in range(5, 13)]
    target_index = 13
    print("Binary search step counts scale with log2(n):")
    for n in sample_sizes:
        data = list(range(n))
        steps, found = binary_search_depth(data, target_index)
        theoretical = max(1, int(log2(n)))
        print(f"n={n:4d}, steps={steps:2d}, log2(n)≈{theoretical:2d}, found={found}")

    unsorted = [5, 1, 9, 2, 6, 3]
    print("\nMerge sort result:", merge_sort(unsorted))

    base = [3, 1, 4, 1, 5, 9, 2, 6]
    tree = build_segment_tree(base)
    size = 1
    while size < len(base):
        size <<= 1
    print("\nSegment tree range sum [2, 6):", range_sum(tree, size, 2, 6))

    # Cross-check with bisect for intuition about logs in library code.
    idx = bisect_left(base, 5)
    print("bisect_left uses binary search internally, index of 5:", idx)
