Feature: Metric Grid Aggregation and Dead Zone Classification
  As a Wi-Fi coverage analyst
  I want to aggregate signal points into spatial grid cells
  So that signal health and dead zone percentages can be calculated

  Scenario: Aggregate measurements into spatial cells
    Given 10 Wi-Fi measurements within a 10m x 10m grid area
    When grid aggregation is performed with a 10m resolution
    Then the cell mean RSSI should equal the arithmetic mean of the measurements

  Scenario: Classify dead zones and survey confidence gaps
    Given a campus boundary containing 10 total grid cells
    And 3 cells have mean RSSI <= -76 dBm
    And 4 cells have fewer measurements than the confidence threshold
    When the coverage statistics are computed
    Then the dead zone percentage should be 30%
    And the coverage gap percentage should be 40%
