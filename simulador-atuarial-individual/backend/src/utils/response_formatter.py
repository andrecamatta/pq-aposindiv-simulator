from typing import Any, Dict, List, Union, Optional
from pydantic import BaseModel
from datetime import datetime, date


class ResponseFormatter:
    """Utility class for standardizing API response formatting"""
    
    @staticmethod
    def format_model_response(
        model: BaseModel, 
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        custom_formatting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a Pydantic model for API response
        
        Args:
            model: Pydantic model instance
            include_fields: Fields to include (if None, include all)
            exclude_fields: Fields to exclude
            custom_formatting: Custom field formatting
            
        Returns:
            Formatted dictionary
        """
        # Get base data
        data = model.model_dump()
        
        # Apply field filtering
        if include_fields:
            data = {k: v for k, v in data.items() if k in include_fields}
        
        if exclude_fields:
            data = {k: v for k, v in data.items() if k not in exclude_fields}
        
        # Apply custom formatting
        if custom_formatting:
            for field, formatter in custom_formatting.items():
                if field in data and callable(formatter):
                    data[field] = formatter(data[field])
        
        return data
    
    @staticmethod
    def format_success_response(
        data: Any = None,
        message: str = "Sucesso",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a successful API response
        
        Args:
            data: Response data
            message: Success message
            metadata: Additional metadata
            
        Returns:
            Standardized success response
        """
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data is not None:
            response["data"] = data
            
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def format_error_response(
        error: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format an error API response
        
        Args:
            error: Error message
            details: Error details
            error_code: Custom error code
            
        Returns:
            Standardized error response
        """
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            response["details"] = details
            
        if error_code:
            response["error_code"] = error_code
            
        return response
    
    @staticmethod
    def format_list_response(
        items: List[Any],
        total_count: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a paginated list response
        
        Args:
            items: List of items
            total_count: Total number of items
            page: Current page number
            page_size: Items per page
            metadata: Additional metadata
            
        Returns:
            Formatted list response
        """
        response = {
            "items": items,
            "count": len(items)
        }
        
        if total_count is not None:
            response["total_count"] = total_count
            
        if page is not None and page_size is not None:
            response["pagination"] = {
                "page": page,
                "page_size": page_size,
                "has_next": total_count is not None and (page * page_size) < total_count,
                "has_previous": page > 1
            }
            
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def sanitize_for_json(obj: Any) -> Any:
        """
        Sanitize objects to be JSON serializable
        
        Args:
            obj: Object to sanitize
            
        Returns:
            JSON-serializable object
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, dict):
            return {k: ResponseFormatter.sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ResponseFormatter.sanitize_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return ResponseFormatter.sanitize_for_json(obj.__dict__)
        else:
            return obj


# Common formatters
def format_currency(value: float, currency: str = "R$") -> str:
    """Format currency values"""
    return f"{currency} {value:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage values"""
    return f"{value * 100:.{decimals}f}%"


def format_date_br(value: Union[datetime, date, str]) -> str:
    """Format dates in Brazilian format"""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    elif isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    
    return value.strftime("%d/%m/%Y")


def format_datetime_br(value: Union[datetime, str]) -> str:
    """Format datetimes in Brazilian format"""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    
    return value.strftime("%d/%m/%Y %H:%M:%S")


# Global instance
response_formatter = ResponseFormatter()