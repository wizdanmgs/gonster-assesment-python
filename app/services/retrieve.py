from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid
from app.db.influx import get_influx_client
from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_historical_data(machine_id: uuid.UUID, start_time: datetime, end_time: datetime, interval: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve historical data from InfluxDB using Flux query.
    """
    async with get_influx_client() as client:
        query_api = client.query_api()
        
        # Base Flux Query to retrieve raw data for the specific machine
        flux_query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> filter(fn: (r) => r["machine_id"] == "{str(machine_id)}")
        '''
        
        # Apply downsampling aggregation window if an 'interval' (like '1h') is provided
        if interval:
            flux_query += f'''
              |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
              |> yield(name: "mean")
            '''
        
        try:
            result = await query_api.query(query=flux_query, org=settings.INFLUXDB_ORG)
            
            # Parse InfluxDB Flux tables into a simple JSON-serializable list
            parsed_data = []
            for table in result:
                for record in table.records:
                    parsed_data.append({
                        "time": record.get_time(),
                        "field": record.get_field(),
                        "value": record.get_value()
                    })
                    
            return parsed_data
        except Exception as e:
            logger.error(f"Failed to query InfluxDB: {str(e)}")
            raise e
