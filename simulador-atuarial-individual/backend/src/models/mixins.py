from typing import Dict, Any
import json


class JSONSerializationMixin:
    """Mixin para padronizar serialização JSON em modelos"""
    
    def get_json_field(self, field_name: str) -> Dict[str, Any]:
        """Deserializa um campo JSON genérico"""
        field_value = getattr(self, field_name)
        if not field_value:
            return {}
        return json.loads(field_value)
    
    def set_json_field(self, field_name: str, data: Dict[str, Any]):
        """Serializa dados para um campo JSON genérico"""
        setattr(self, field_name, json.dumps(data))
    
    def get_json_field_with_transform(self, field_name: str, key_transform=None, value_transform=None) -> Dict:
        """
        Deserializa com transformações opcionais nas chaves/valores
        
        Args:
            field_name: Nome do campo JSON
            key_transform: Função para transformar chaves (ex: int, str)
            value_transform: Função para transformar valores
        """
        data = self.get_json_field(field_name)
        
        if not data:
            return {}
            
        result = {}
        for k, v in data.items():
            new_key = key_transform(k) if key_transform else k
            new_value = value_transform(v) if value_transform else v
            result[new_key] = new_value
            
        return result
    
    def set_json_field_with_transform(self, field_name: str, data: Dict, key_transform=None, value_transform=None):
        """
        Serializa com transformações opcionais nas chaves/valores
        
        Args:
            field_name: Nome do campo JSON  
            data: Dados a serem serializados
            key_transform: Função para transformar chaves (ex: str)
            value_transform: Função para transformar valores
        """
        if not data:
            setattr(self, field_name, json.dumps({}))
            return
            
        transformed = {}
        for k, v in data.items():
            new_key = key_transform(k) if key_transform else k
            new_value = value_transform(v) if value_transform else v
            transformed[new_key] = new_value
            
        setattr(self, field_name, json.dumps(transformed))