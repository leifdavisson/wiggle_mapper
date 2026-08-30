Feature: WiGLE CSV Ingestion and Filtering
  As a network surveyor
  I want to parse WiGLE CSV files and filter Wi-Fi data
  So that school network coverage can be mapped accurately

  Scenario: Parse standard WiGLE CSV with pre-header metadata
    Given a WiGLE CSV file containing 2 header lines and 3 Wi-Fi records
    When the CSV parser processes the content
    Then 3 valid Wi-Fi data points should be returned
    And non-Wi-Fi records or invalid coordinates should be omitted

  Scenario: Filter points by SSID and Frequency Band
    Given a dataset with mixed 2.4 GHz and 5 GHz networks
    When filtered for SSID "School-WiFi" and 5 GHz band only
    Then only points matching "School-WiFi" with frequency >= 4900 MHz should remain
