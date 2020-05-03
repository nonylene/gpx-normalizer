import argparse
import datetime
from typing import List

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


def interval_normalized_points(points: List[gpxpy.gpx.GPXTrackPoint], interval: float) -> List[gpxpy.gpx.GPXTrackPoint]:
    # init
    normalized_points = [points[0]]
    previous_point = points[0]
    next_time: datetime.datetime = points[0].time + datetime.timedelta(seconds=interval)

    for point in points[1:]:
        time_delta = point.time - previous_point.time
        lat_delta = point.latitude - previous_point.latitude
        long_delta = point.longitude - previous_point.longitude
        elv_delta = point.elevation - previous_point.elevation

        while next_time <= point.time:
            if next_time == point.time:
                normalized_points.append(point)
            else:
                # Interpolate (Conformal route) and append
                # Interpolated values: elevate, lattitude, longtitude
                ratio = (next_time - previous_point.time) / time_delta
                interpolated_point = gpxpy.gpx.GPXTrackPoint(
                    latitude=previous_point.latitude + lat_delta * ratio,
                    longitude=previous_point.longitude + long_delta * ratio,
                    elevation=previous_point.elevation + elv_delta * ratio,
                    time=next_time,
                )
                normalized_points.append(interpolated_point)

            # Go to next time
            next_time += datetime.timedelta(seconds=interval)

        # Go to next point
        previous_point = point

    return normalized_points


def main(input_file: str, output_file: str, max_speed: float, interval: float):
    with open(input_file) as f:
        in_gpx = gpxpy.parse(f)

    for track in in_gpx.tracks:
        for segment in track.segments:
            remove_far_points(segment, max_speed)
            new_points = interval_normalized_points(segment.points, interval)
            segment.points = new_points

    with open(output_file, mode="w") as f:
        f.write(in_gpx.to_xml())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input_file", type=str, required=True, help="Input GPX file path")
    parser.add_argument("-o", "--output", dest="output_file", type=str, required=True, help="Output GPX file path")
    parser.add_argument("-s", "--max-speed", dest="max_speed", type=float, default=100, help="Max speed (km/h)")
    parser.add_argument("-t", "--interval", dest="interval", type=float, default=30, help="Interval (s)")
    args = parser.parse_args()

    main(args.input_file, args.output_file, args.max_speed, args.interval)
