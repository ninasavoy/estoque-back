from enum import Enum
from typing import List, Set
from fastapi import HTTPException, status

class UserType(str, Enum):
    FARMACEUTICA = "farmaceutica"
    DISTRIBUIDOR = "distribuidor"
    SUS = "sus"
    UBS = "ubs"
    PACIENTE = "paciente"


class Permission(str, Enum):
    # Medicamentos
    CREATE_MEDICAMENTO = "create_medicamento"
    READ_MEDICAMENTO = "read_medicamento"
    UPDATE_MEDICAMENTO = "update_medicamento"
    DELETE_MEDICAMENTO = "delete_medicamento"
    
    # Lotes
    CREATE_LOTE = "create_lote"
    READ_LOTE = "read_lote"
    UPDATE_LOTE = "update_lote"
    DELETE_LOTE = "delete_lote"
    
    # Check-in (Movimentações)
    CHECKIN_DISTRIBUIDOR_SUS = "checkin_distribuidor_sus"
    CHECKIN_SUS_UBS = "checkin_sus_ubs"
    CHECKIN_UBS_PACIENTE = "checkin_ubs_paciente"
    
    # Visualização de movimentações
    VIEW_ALL_MOVIMENTACOES = "view_all_movimentacoes"
    VIEW_OWN_MOVIMENTACOES = "view_own_movimentacoes"
    
    # Dashboards
    VIEW_FARMACEUTICA_DASHBOARD = "view_farmaceutica_dashboard"
    VIEW_DISTRIBUIDOR_DASHBOARD = "view_distribuidor_dashboard"
    VIEW_SUS_DASHBOARD = "view_sus_dashboard"
    VIEW_UBS_DASHBOARD = "view_ubs_dashboard"
    
    # Feedbacks
    CREATE_FEEDBACK = "create_feedback"
    READ_ALL_FEEDBACKS = "read_all_feedbacks"
    READ_OWN_FEEDBACKS = "read_own_feedbacks"
    
    # Gestão de usuários
    MANAGE_USERS = "manage_users"
    
    # Estoque
    VIEW_ESTOQUE = "view_estoque"
    MANAGE_ESTOQUE = "manage_estoque"
    
    # Canal de comunicação
    ACCESS_COMMUNICATION_CHANNEL = "access_communication_channel"


# Mapeamento de permissões por tipo de usuário
PERMISSIONS_MAP: dict[UserType, Set[Permission]] = {
    UserType.FARMACEUTICA: {
        # Dona da aplicação - acesso total
        Permission.CREATE_MEDICAMENTO,
        Permission.READ_MEDICAMENTO,
        Permission.UPDATE_MEDICAMENTO,
        Permission.DELETE_MEDICAMENTO,
        Permission.CREATE_LOTE,
        Permission.READ_LOTE,
        Permission.UPDATE_LOTE,
        Permission.DELETE_LOTE,
        Permission.VIEW_ALL_MOVIMENTACOES,
        Permission.VIEW_FARMACEUTICA_DASHBOARD,
        Permission.READ_ALL_FEEDBACKS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ESTOQUE,
        Permission.MANAGE_ESTOQUE,
        Permission.ACCESS_COMMUNICATION_CHANNEL,
    },
    
    UserType.DISTRIBUIDOR: {
        # Parceiro - foco em logística
        Permission.READ_MEDICAMENTO,
        Permission.READ_LOTE,
        Permission.CHECKIN_DISTRIBUIDOR_SUS,
        Permission.VIEW_OWN_MOVIMENTACOES,
        Permission.VIEW_DISTRIBUIDOR_DASHBOARD,
    },
    
    UserType.SUS: {
        # Gestão regional - check-in e dashboards gerenciais
        Permission.READ_MEDICAMENTO,
        Permission.READ_LOTE,
        Permission.CHECKIN_SUS_UBS,
        Permission.VIEW_OWN_MOVIMENTACOES,
        Permission.VIEW_SUS_DASHBOARD,
        Permission.VIEW_ESTOQUE,
        Permission.MANAGE_ESTOQUE,
    },
    
    UserType.UBS: {
        # Unidade de saúde - controle de estoque local
        Permission.READ_MEDICAMENTO,
        Permission.READ_LOTE,
        Permission.CHECKIN_UBS_PACIENTE,
        Permission.VIEW_OWN_MOVIMENTACOES,
        Permission.VIEW_UBS_DASHBOARD,
        Permission.VIEW_ESTOQUE,
    },
    
    UserType.PACIENTE: {
        # Paciente final - check-in e comunicação
        Permission.READ_MEDICAMENTO,  # Informações sobre seu medicamento
        Permission.CHECKIN_UBS_PACIENTE,  # Confirmar recebimento
        Permission.CREATE_FEEDBACK,
        Permission.READ_OWN_FEEDBACKS,
        Permission.ACCESS_COMMUNICATION_CHANNEL,
    },
}


def has_permission(user_type: str, permission: Permission) -> bool:
    """Verifica se um tipo de usuário tem uma permissão específica"""
    try:
        user_type_enum = UserType(user_type)
        return permission in PERMISSIONS_MAP.get(user_type_enum, set())
    except ValueError:
        return False


def require_permissions(required_permissions: List[Permission]):
    """Decorator para verificar permissões em rotas"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Obtém o usuário atual dos kwargs (injetado por dependency)
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Não autenticado"
                )
            
            user_type = current_user.tipo
            
            # Verifica se o usuário tem todas as permissões necessárias
            for permission in required_permissions:
                if not has_permission(user_type, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Sem permissão: {permission.value}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_user_permissions(user_type: str) -> List[str]:
    """Retorna todas as permissões de um tipo de usuário"""
    try:
        user_type_enum = UserType(user_type)
        return [p.value for p in PERMISSIONS_MAP.get(user_type_enum, set())]
    except ValueError:
        return []


# Permissões específicas por recurso
class ResourcePermissions:
    """Classe helper para verificações de permissões específicas"""
    
    @staticmethod
    def can_view_dashboard(user_type: str) -> str:
        """Retorna qual dashboard o usuário pode acessar"""
        dashboards = {
            UserType.FARMACEUTICA: "farmaceutica",
            UserType.DISTRIBUIDOR: "distribuidor",
            UserType.SUS: "sus",
            UserType.UBS: "ubs",
        }
        try:
            return dashboards.get(UserType(user_type), None)
        except ValueError:
            return None
    
    @staticmethod
    def can_checkin_for_stage(user_type: str) -> str:
        """Retorna em qual estágio o usuário pode fazer check-in"""
        checkin_stages = {
            UserType.DISTRIBUIDOR: "distribuidor_sus",
            UserType.SUS: "sus_ubs",
            UserType.UBS: "ubs_paciente",
            UserType.PACIENTE: "paciente_confirm",
        }
        try:
            return checkin_stages.get(UserType(user_type), None)
        except ValueError:
            return None
    
    @staticmethod
    def get_visible_data_scope(user_type: str) -> str:
        """Define o escopo de dados visíveis para cada usuário"""
        scopes = {
            UserType.FARMACEUTICA: "all",  # Vê todos os dados
            UserType.DISTRIBUIDOR: "own_operations",  # Apenas suas operações
            UserType.SUS: "regional",  # Dados da região
            UserType.UBS: "local",  # Dados da unidade
            UserType.PACIENTE: "personal",  # Apenas seus dados
        }
        try:
            return scopes.get(UserType(user_type), "none")
        except ValueError:
            return "none"