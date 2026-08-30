Feature: Geodesic Spatial Calculations and Geometry
  As an automated mapping engine
  I want to compute metric distances, polygon containment, and convex hulls
  So that campus boundaries and spatial grids are mathematically sound

  Scenario: Verify Point-In-Polygon containment
    Given a rectangular campus boundary polygon
    When checking a coordinate located inside the boundary
    Then the ray-casting algorithm returns True
    When checking a coordinate located outside the boundary
    Then the ray-casting algorithm returns False

  Scenario: Generate Convex Hull using Andrew's Monotone Chain
    Given a set of 5 non-collinear campus coordinates
    When Andrew's Monotone Chain algorithm is executed
    Then a minimal convex hull polygon enclosing all points is constructed
