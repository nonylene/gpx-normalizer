import argparse

import gpxpy


def calc_2d_speed(one: gpxpy.gpx.GPXTrackSegment, two: gpxpy.gpx.GPXTrackSegment) -> float:
    """
    m/s
    """
    # Calculate 2D speed
    time_difference = one.time_difference(two)
    distance = one.distance_2d(two)
    if time_difference == 0:
        return float('inf')

    return distance / time_difference


def remove_far_points(segment: gpxpy.gpx.GPXTrackSegment, max_speed: float) -> None:
    """
    remove_far_points uses the point and the previous point to calculate speed.
    This ignores elevation because that data in Google Location History logs are unstable.
    """
    i = 0
    while i < len(segment.points):
        if i == 0:
            i += 1
            continue

        point: gpxpy.gpx.GPXTrackPoint = segment.points[i]
        previous_point: gpxpy.gpx.GPXTrackPoint = segment.points[i-1]

        # m/s -> km/h
        speed = calc_2d_speed(point, previous_point) * 3600 / 1000
        if speed > max_speed:
            segment.remove_point(i)
            continue

        i += 1


def main(input_file: str, output_file: str, max_speed: float):
    with open(input_file) as f:
        in_gpx = gpxpy.parse(f)

    for track in in_gpx.tracks:
        for segment in track.segments:
            remove_far_points(segment, max_speed)

    with open(output_file, mode="w") as f:
        f.write(in_gpx.to_xml())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input_file", type=str, required=True, help="Input GPX file path")
    parser.add_argument("-o", "--output", dest="output_file", type=str, required=True, help="Output GPX file path")
    parser.add_argument("-s", "--max-speed", dest="max_speed", type=float, default=100, help="Max speed (km/h)")
    args = parser.parse_args()

    main(args.input_file, args.output_file, args.max_speed)
