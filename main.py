from package.llm_postprocessor import PostProcessor, BatchFileProcessor

if __name__ == "__main__":
    batch_processor = BatchFileProcessor()
    print("Starting batch processing of all session1 data...")
    print("=" * 80)
    stats = batch_processor.process_data_folder(
        data_folder="data",
        output_folder="post_processed",
        session_number=1,
    )