import json
from chatx.genie_result import GenieResult
from databricks.sdk.service.sql import (
    StatementResponse,
    ColumnInfoTypeName,
    ResultData,
    ResultManifest,
    ResultSchema,
    ColumnInfo,
)
from databricks.sdk.service.dashboards import GenieResultMetadata


def test_genie_result() -> None:
    result = GenieResult(
        query_description="Test Query",
        query_result_metadata=GenieResultMetadata(row_count=5),
        statement_response=StatementResponse(
            result=ResultData(
                data_array=[
                    [1, "Alice", 100.0],
                    [2, "Bob", 200.0],
                    [3, "Charlie", 300.0],
                ]
            ),
            manifest=ResultManifest(
                schema=ResultSchema(
                    columns=[
                        ColumnInfo(name="id", type_name=ColumnInfoTypeName.INT),
                        ColumnInfo(name="name", type_name=ColumnInfoTypeName.STRING),
                        ColumnInfo(name="amount", type_name=ColumnInfoTypeName.DOUBLE),
                    ]
                )
            ),
        ),
    )
    response = json.dumps(result.process_query_results().as_dict())
    
    assert "1" in response
    assert "Alice" in response
    assert "100.00" in response
    assert "2" in response
    assert "Bob" in response
    assert "200.00" in response  

    assert "**Row Count:** 5" in response


def test_genie_result_with_null_values():
    """Test NULL value formatting - covers line 81"""
    result = GenieResult(
        query_description="Test Query with NULL values",
        statement_response=StatementResponse(
            result=ResultData(
                data_array=[
                    [1, None, "test"],  # None value to trigger line 81
                    [2, "Bob", None],   # Another None to test thoroughly
                ]
            ),
            manifest=ResultManifest(
                schema=ResultSchema(
                    columns=[
                        ColumnInfo(name="id", type_name=ColumnInfoTypeName.INT),
                        ColumnInfo(name="name", type_name=ColumnInfoTypeName.STRING),
                        ColumnInfo(name="value", type_name=ColumnInfoTypeName.STRING),
                    ]
                )
            ),
        ),
    )
    
    response = json.dumps(result.process_query_results().as_dict())
    
    # Verify NULL values are properly formatted
    assert "NULL" in response
    assert "1" in response  # First row ID
    assert "2" in response  # Second row ID
    assert "test" in response  # Non-null string value


def test_genie_result_missing_manifest():
    """Test warning when manifest is missing - covers line 61"""
    result = GenieResult(
        query_description="Test Query with missing manifest",
        statement_response=StatementResponse(
            result=ResultData(
                data_array=[
                    [1, "test"],
                ]
            ),
            # manifest=None (default) - Missing manifest to trigger line 61
        ),
    )
    
    # Process the result - this should trigger the warning log on line 61
    activity = result.process_query_results()
    
    # The test should still complete successfully even with missing manifest
    # It will use empty columns list and create basic table
    assert activity.text is not None or hasattr(activity, 'attachments')


def test_genie_result_missing_result():
    """Test error logging when result/data_array missing - covers lines 104-106"""
    result = GenieResult(
        query_description="Test Query with missing result",
        statement_response=StatementResponse(
            # result=None (default) - Missing result to trigger error path
        ),
    )
    
    # Process the result - this should trigger error logging on lines 104-106
    activity = result.process_query_results()
    
    # Should return a basic text activity (not table card) since result is missing
    assert activity.type == "message"
    assert "Test Query with missing result" in activity.text


def test_genie_result_message_only():
    """Test message-only response - covers lines 107-112"""
    result = GenieResult(
        message="This is a simple message response",
        # No statement_response - triggers message-only path
    )
    
    activity = result.process_query_results()
    
    # Should return message-type activity
    assert activity.type == "message"
    assert "This is a simple message response" in activity.text


def test_genie_result_no_data_fallback():
    """Test fallback when no statement_response or message - covers lines 113-117"""
    result = GenieResult(
        query_description="Just a description, no data",
        # No statement_response, no message - triggers fallback
    )
    
    activity = result.process_query_results()
    
    # Should return fallback message
    assert activity.type == "message"
    assert "No data available." in activity.text
    assert "Just a description, no data" in activity.text
      
