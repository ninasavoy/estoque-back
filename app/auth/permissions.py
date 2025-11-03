from enum import Enum
from typing import List, Set
from fastapi import HTTPException, status

class UserType(str, Enum):
    ADMIN = "admin"
    FARMACEUTICA = "farmaceutica"
    DISTRIBUIDOR = "distribuidor"
    SUS = "sus"
    UBS = "ubs"
    PACIENTE = "paciente"


from enum import Enum

class Permission(str, Enum):
    # Famacêuticas
    CREATE_FARMACEUTICA = "create_farmaceutica"
    LIST_FARMACEUTICA = "list_farmaceutica"
    UPDATE_FARMACEUTICA = "update_farmaceutica"
    DELETE_FARMACEUTICA = "delete_farmaceutica"

    # Distribuidores
    CREATE_DISTRIBUIDOR = "create_distribuidor"
    LIST_DISTRIBUIDOR = "list_distribuidor"
    UPDATE_DISTRIBUIDOR = "update_distribuidor"
    DELETE_DISTRIBUIDOR = "delete_distribuidor"

    # SUS
    CREATE_SUS = "create_sus"
    LIST_SUS = "list_sus"
    UPDATE_SUS = "update_sus"
    DELETE_SUS = "delete_sus"

    # UBS
    CREATE_UBS = "create_ubs"
    LIST_UBS = "list_ubs"
    UPDATE_UBS = "update_ubs"
    DELETE_UBS = "delete_ubs"

    # Pacientes
    CREATE_PACIENTE = "create_paciente"
    LIST_PACIENTE = "list_paciente"
    UPDATE_PACIENTE = "update_paciente"
    DELETE_PACIENTE = "delete_paciente"

    # Medicamentos
    CREATE_MEDICAMENTO = "create_medicamento"
    LIST_MEDICAMENTO = "list_medicamento"
    UPDATE_MEDICAMENTO = "update_medicamento"
    DELETE_MEDICAMENTO = "delete_medicamento"

    # Lotes
    CREATE_LOTE = "create_lote"
    LIST_LOTE = "list_lote"
    UPDATE_LOTE = "update_lote"
    DELETE_LOTE = "delete_lote"

    # Movimentações Distribuição para SUS
    CREATE_MOVIMENTACAO_DS = "create_movimentacao_ds"
    LIST_MOVIMENTACAO_DS = "list_movimentacao_ds"
    UPDATE_MOVIMENTACAO_DS = "update_movimentacao_ds"
    DELETE_MOVIMENTACAO_DS = "delete_movimentacao_ds"

    # Movimentações SUS para UBS
    CREATE_MOVIMENTACAO_SU = "create_movimentacao_su"
    LIST_MOVIMENTACAO_SU = "list_movimentacao_su"
    UPDATE_MOVIMENTACAO_SU = "update_movimentacao_su"
    DELETE_MOVIMENTACAO_SU = "delete_movimentacao_su"

    # Movimentações UBS para Paciente
    CREATE_MOVIMENTACAO_UP = "create_movimentacao_up"
    LIST_MOVIMENTACAO_UP = "list_movimentacao_up"
    UPDATE_MOVIMENTACAO_UP = "update_movimentacao_up"
    DELETE_MOVIMENTACAO_UP = "delete_movimentacao_up"

    # Estoque
    VIEW_ESTOQUE = "view_estoque"
    MANAGE_ESTOQUE = "manage_estoque"

    # Dashboards
    VIEW_FARMACEUTICA_DASHBOARD = "view_farmaceutica_dashboard"
    VIEW_DISTRIBUIDOR_DASHBOARD = "view_distribuidor_dashboard"
    VIEW_SUS_DASHBOARD = "view_sus_dashboard"
    VIEW_UBS_DASHBOARD = "view_ubs_dashboard"

    # Usuários
    MANAGE_USERS = "manage_users"

    # Comunicação / Feedback
    CREATE_FEEDBACK = "create_feedback"
    READ_ALL_FEEDBACKS = "read_all_feedbacks"
    READ_OWN_FEEDBACKS = "read_own_feedbacks"
    ACCESS_COMMUNICATION_CHANNEL = "access_communication_channel"



# Mapeamento de permissões por tipo de usuário
PERMISSIONS_MAP: dict[UserType, Set[Permission]] = {
    UserType.ADMIN: set(p for p in Permission),  # Acesso total
    
    UserType.FARMACEUTICA: {
        # só pode criar e visualizar seus próprios usuários e medicamentos

        # farmacêuticas
        Permission.CREATE_FARMACEUTICA,
        Permission.LIST_FARMACEUTICA,
        Permission.UPDATE_FARMACEUTICA,
        Permission.DELETE_FARMACEUTICA, 

        # medicamentos
        Permission.CREATE_MEDICAMENTO,
        Permission.LIST_MEDICAMENTO, 
        Permission.UPDATE_MEDICAMENTO, 
        Permission.DELETE_MEDICAMENTO,

        # lotes
        Permission.CREATE_LOTE,
        Permission.LIST_LOTE,
        Permission.UPDATE_LOTE,
        Permission.DELETE_LOTE,
        
        # movimentações distribuidor -> sus
        Permission.CREATE_MOVIMENTACAO_DS,
        Permission.LIST_MOVIMENTACAO_DS,
        Permission.UPDATE_MOVIMENTACAO_DS,
        Permission.DELETE_MOVIMENTACAO_DS,

        # movimentações sus -> ubs
        Permission.CREATE_MOVIMENTACAO_SU,
        Permission.LIST_MOVIMENTACAO_SU,
        Permission.UPDATE_MOVIMENTACAO_SU,
        Permission.DELETE_MOVIMENTACAO_SU,

        # movimentações ubs -> paciente
        Permission.CREATE_MOVIMENTACAO_UP,
        Permission.LIST_MOVIMENTACAO_UP,
        Permission.UPDATE_MOVIMENTACAO_UP,
        Permission.DELETE_MOVIMENTACAO_UP,
        
        # Permission.VIEW_FARMACEUTICA_DASHBOARD,
    },
    
    UserType.DISTRIBUIDOR: {
        # distribuidores podem ver lotes e gerenciar suas movimentações
        
        # distribuidores
        Permission.CREATE_DISTRIBUIDOR,
        Permission.LIST_DISTRIBUIDOR,
        Permission.UPDATE_DISTRIBUIDOR,
        Permission.DELETE_DISTRIBUIDOR,

        Permission.LIST_LOTE,
        Permission.CREATE_MOVIMENTACAO_DS,
        Permission.LIST_MOVIMENTACAO_DS,
        Permission.UPDATE_MOVIMENTACAO_DS,
        Permission.DELETE_MOVIMENTACAO_DS,

        # Permission.VIEW_DISTRIBUIDOR_DASHBOARD,
    },
    
    UserType.SUS: {
        # sus podem ver lotes e gerenciar suas movimentações
        
        # sus
        Permission.CREATE_SUS,
        Permission.LIST_SUS,
        Permission.UPDATE_SUS,
        Permission.DELETE_SUS,

        Permission.LIST_LOTE,
        # Permission.CHECKIN_SUS_UBS,
        Permission.VIEW_SUS_DASHBOARD,
        Permission.VIEW_ESTOQUE,
    },
    
    UserType.UBS: {
        # Permission.READ_LOTE,
        # Permission.CHECKIN_UBS_PACIENTE,
        Permission.VIEW_UBS_DASHBOARD,
        Permission.VIEW_ESTOQUE,
    },
    
    UserType.PACIENTE: {
        # Permission.READ_MEDICAMENTO,
        Permission.CREATE_FEEDBACK,
        Permission.READ_OWN_FEEDBACKS,
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
    
    # @staticmethod
    # def get_visible_data_scope(user_type: str) -> str:
    #     """Define o escopo de dados visíveis para cada tipo de usuário."""
    #     scopes = {
    #         UserType.ADMIN: "all",            # vê tudo
    #         UserType.FARMACEUTICA: "own",     # vê só seus medicamentos e lotes
    #         UserType.DISTRIBUIDOR: "own_ops", # vê só suas movimentações
    #         UserType.SUS: "regional",         # vê SUS e UBS da sua região
    #         UserType.UBS: "local",            # vê só os dados da própria unidade
    #         UserType.PACIENTE: "personal",    # vê só seus dados
    #     }
    #     return scopes.get(UserType(user_type), "none")


    # //////////////////////////////////////////////////////////////////////

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