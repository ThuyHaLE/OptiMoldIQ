from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent

class DataPipelineOrchestrator:
    def __init__(self, 
                 dynamic_db_source_dir="database/dynamicDatabase",
                 databaseSchemas_path: str = "database/databaseSchemas.json",
                 annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
                 default_dir: str = "agents/shared_db"
                 ):
        
        self.dynamic_db_source_dir = dynamic_db_source_dir
        self.databaseSchemas_path = databaseSchemas_path
        self.annotation_path = annotation_path
        self.default_dir = default_dir

    def run_pipeline(self, **kwargs):
        DataCollector(self.dynamic_db_source_dir,
                      self.default_dir)

        DataLoaderAgent(self.databaseSchemas_path,
                        self.annotation_path,
                        self.default_dir)