from package.llm_postprocessor.postprocessor.processor import BatchFileProcessor

processor = BatchFileProcessor()
stats = processor.process_data_folder(
    data_folder="data",         
    output_folder="post_processed",
    session_number=1,          
)
print(stats)