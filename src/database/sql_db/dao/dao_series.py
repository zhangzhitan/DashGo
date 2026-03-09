from peewee import DoesNotExist, IntegrityError
from common.utilities.util_logger import Log
from ..conn import db
from ..entity.table_goods import DimIP, DimSeries

logger = Log.get_logger(__name__)

def get_all_series():
    """获取所有系列，包含关联的IP名称，返回字典列表"""
    query = (DimSeries
             .select(DimIP.ip_name, DimSeries.series_name, DimSeries.series_batch, DimSeries.series_remark)
             .join(DimIP)
             .dicts())
    return list(query)

def exists_series(ip_name: str, series_name: str) -> bool:
    """检查特定IP下该系列是否已存在"""
    try:
        ip = DimIP.get(DimIP.ip_name == ip_name)
        DimSeries.get(DimSeries.ip == ip, DimSeries.series_name == series_name)
        return True
    except DoesNotExist:
        return False

def ensure_ip_exists(ip_name: str):
    """【核心扩展】确保IP存在，如果不存在则自动创建"""
    try:
        DimIP.get(DimIP.ip_name == ip_name)
    except DoesNotExist:
        logger.info(f"IP '{ip_name}' 不存在，正在自动创建...")
        DimIP.create(ip_name=ip_name, ip_remark="创建系列时自动补充")

def create_series(ip_name: str, series_name: str, series_batch: str, series_remark: str) -> bool:
    """新建系列（自动补充缺失IP）"""
    database = db()
    with database.atomic() as txn:
        try:
            ensure_ip_exists(ip_name)
            ip = DimIP.get(DimIP.ip_name == ip_name)
            DimSeries.create(ip=ip, series_name=series_name, series_batch=series_batch, series_remark=series_remark)
            txn.commit()
            return True
        except IntegrityError as e:
            logger.warning(f'创建系列 {series_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def update_series(old_ip_name: str, old_series_name: str, new_ip_name: str, new_series_name: str, series_batch: str, remark: str) -> bool:
    """更新系列信息（包含修改所属IP，并自动补充缺失IP）"""
    database = db()
    with database.atomic() as txn:
        try:
            ensure_ip_exists(new_ip_name)
            
            old_ip = DimIP.get(DimIP.ip_name == old_ip_name)
            series = DimSeries.get(DimSeries.ip == old_ip, DimSeries.series_name == old_series_name)
            
            new_ip = DimIP.get(DimIP.ip_name == new_ip_name)
            series.ip = new_ip
            series.series_name = new_series_name
            series.series_batch = series_batch
            series.series_remark = remark
            series.save()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'更新系列 {old_series_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def delete_series(ip_name: str, series_name: str) -> bool:
    """删除系列"""
    database = db()
    with database.atomic() as txn:
        try:
            ip = DimIP.get(DimIP.ip_name == ip_name)
            DimSeries.delete().where(DimSeries.ip == ip, DimSeries.series_name == series_name).execute()
            txn.commit()
            return True
        except Exception as e:
            logger.warning(f'删除系列 {series_name} 时出现异常: {e}', exc_info=True)
            txn.rollback()
            return False

def batch_import_series(records: list) -> tuple[bool, str]:
    """批量导入系列（自动补充缺失IP）"""
    database = db()
    with database.atomic() as txn:
        try:
            success_count = 0
            for row in records:
                ip_name = str(row.get('ip_name', '')).strip()
                series_name = str(row.get('series_name', '')).strip()
                batch = str(row.get('series_batch', ''))
                remark = str(row.get('series_remark', ''))
                
                if ip_name and series_name and not exists_series(ip_name, series_name):
                    ensure_ip_exists(ip_name)
                    ip = DimIP.get(DimIP.ip_name == ip_name)
                    DimSeries.create(ip=ip, series_name=series_name, series_batch=batch, series_remark=remark)
                    success_count += 1
            txn.commit()
            return True, f"成功导入 {success_count} 条新数据（已自动补充缺失IP）。"
        except Exception as e:
            logger.error(f"批量导入系列失败: {e}", exc_info=True)
            txn.rollback()
            return False, "导入失败，请检查数据格式。"