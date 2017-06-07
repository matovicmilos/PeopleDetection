def get_range(self, correlations, F, P1, P2):
    """
    Using the set of correlations produced by correlate_lines, identify the range of the lines in the scene.

    :param correlations: List of correlations, each element a list of one or more pairs of points, to use to
                         calculate distances
    :returns: A dict, keyed by correlation, with the distances for each correlated point.
    """

    # The results are indexed against the points in both left and right images for ease of display
    left_range, right_range = {}, {}

    for left_group, right_group in correlations:
        # multiple intersection points are provided, average out the distances
        left_corrected, right_corrected = cv2.correctMatches(F, np.array([left_group]), np.array([right_group]))
        collection = cv2.triangulatePoints(P1, P2, left_corrected, right_corrected)
        triangulated = np.mean(collection, axis=1).reshape(4, 1)  # Average the results of the triangulation

        # homo to normal coords by dividing by last element. squares are 28mm.
        in_mm = (triangulated[0:3] / triangulated[3]) * 28
        x, y, z = (float(n) for n in in_mm)

        # z <= 0 means behind the camera -- not actually possible.
        if z > 0:
            distance = (x ** 2 + y ** 2 + z ** 2) ** 0.5  # length of vector to get distance to object

            # reference the distance against the average of the intersection points for each image.
            left_range[tuple(np.mean(left_group, axis=0))] = (distance, x, y, z)
            right_range[tuple(np.mean(right_group, axis=0))] = (distance, x, y, z)

    return left_range, right_range



# Here it is. The 'correlations' parameter is the point(s) in the left/right images that are of the same thing.
#
# e.g. the thing being measured is at 130,200 in the left image and 137,201 in the right image then correlations would be [[(130, 200)], [(137, 201)]]. Multiple point pairs are supported, where the distance calculated is averaged to smooth out any faults.
