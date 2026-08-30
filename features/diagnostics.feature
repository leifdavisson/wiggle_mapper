Feature: Diagnostic Alerts and Project Serialization
  As a network administrator
  I want automated diagnostic alerts and reliable project import/export
  So that network issues are flagged and projects can be saved

  Scenario: Detect high 2.4 GHz channel congestion
    Given channel 6 has 7 distinct active BSSID transmitters
    When diagnostic analysis is executed
    Then a warning alert for channel 6 congestion should be generated

  Scenario: Serialize and deserialize project configuration
    Given an active project with 50 points, 4 boundary vertices, and 2 files
    When the project state is exported to JSON and re-imported
    Then the imported project state matches the original exactly
