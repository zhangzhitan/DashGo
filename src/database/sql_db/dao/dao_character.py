from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..conn import db
from ..entity.table_goods import DimIP, DimCharacter

logger = Log.get_logger(__name__)

def get_all_characters():
    """获取所有角色，包含关联的IP名称，返回字典列表"""
    query = (DimCharacter
             .select(DimIP.ip_name, DimCharacter.character_name, DimCharacter.character_remark)
             .join(DimIP)
             .dicts())
    return list(query)

def exists_character(ip_name: str, character_name: str) -> bool:
    """检查特定IP下该角色是否已存在"""
    try:
        ip = DimIP.get(DimIP.ip_name == ip_name)
        DimCharacter.get(DimCharacter.ip == ip, DimCharacter.character_name == character_name)
        return True
    except DoesNotExist:
        return False

def ensure_ip_exists(ip_name: str):
    """【核心扩展】确保IP存在，如果不存在则自动创建"""
    try:
        DimIP.get(DimIP.ip_name == ip_name)
    except DoesNotExist:
        logger.info(f"IP '{ip_name}' 不存在，正在自动创建...")
        DimIP.create(ip_name=ip_name, ip_remark="创建角色时自动补充")

def create_character(ip_name: str, character_name: str, character_remark: str) -> bool:
    """新建角色（自动补充缺失IP）"""
    database = db()
    with database.atomic() as txn:
        try:
            ensure_ip_exists(ip_name)
            ip = DimIP.get(DimIP.ip_name == ip_name)
            DimCharacter.create(ip=ip, character_name=character_name, character_remark=character_remark)
            txn.commit()
            return True
        except IntegrityError as e:
            logger.warning(f'创建角色 {character_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def update_character(old_ip_name: str, old_char_name: str, new_ip_name: str, new_char_name: str, remark: str) -> bool:
    """更新角色信息（包含修改所属IP，并自动补充缺失IP）"""
    database = db()
    with database.atomic() as txn:
        try:
            # 确保新的IP存在
            ensure_ip_exists(new_ip_name)
            
            old_ip = DimIP.get(DimIP.ip_name == old_ip_name)
            char = DimCharacter.get(DimCharacter.ip == old_ip, DimCharacter.character_name == old_char_name)
            
            new_ip = DimIP.get(DimIP.ip_name == new_ip_name)
            char.ip = new_ip
            char.character_name = new_char_name
            char.character_remark = remark
            char.save()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'更新角色 {old_char_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def delete_character(ip_name: str, character_name: str) -> bool:
    """删除角色"""
    database = db()
    with database.atomic() as txn:
        try:
            ip = DimIP.get(DimIP.ip_name == ip_name)
            DimCharacter.delete().where(DimCharacter.ip == ip, DimCharacter.character_name == character_name).execute()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'删除角色 {character_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def batch_import_characters(records: list) -> tuple[bool, str]:
    """批量导入角色（自动补充缺失IP）"""
    database = db()
    with database.atomic() as txn:
        try:
            success_count = 0
            for row in records:
                ip_name = str(row.get('ip_name', '')).strip()
                char_name = str(row.get('character_name', '')).strip()
                remark = str(row.get('character_remark', ''))
                
                if ip_name and char_name and not exists_character(ip_name, char_name):
                    ensure_ip_exists(ip_name)
                    ip = DimIP.get(DimIP.ip_name == ip_name)
                    DimCharacter.create(ip=ip, character_name=char_name, character_remark=remark)
                    success_count += 1
            txn.commit()
            return True, f"成功导入 {success_count} 条新数据（已自动补充缺失IP）。"
        except Exception as e:
            logger.error(f"批量导入角色失败: {e}", exc_info=True)
            txn.rollback()
            return False, "导入失败，请检查数据格式。"