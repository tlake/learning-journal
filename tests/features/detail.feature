Feature: Detail
    A display of the title, date, and contents of a journal entry


Scenario: Entries written with MarkDown are formatted for display
    Given an authenticated user
    And a journal entry written using MarkDown syntax
    When they visit the detail view
    Then the entry will have converted the MarkDown to HTML