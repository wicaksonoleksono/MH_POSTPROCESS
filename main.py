from package.llm_postprocessor import PostProcessor, BatchFileProcessor

if __name__ == "__main__":
    # Process all session1 folders from data/ and save to post_processed/
    batch_processor = BatchFileProcessor()

    print("Starting batch processing of all session1 data...")
    print("=" * 80)

    stats = batch_processor.process_data_folder(
        data_folder="data",
        output_folder="post_processed",
        session_number=1,
    )

    print("=" * 80)
    print(f"\nBatch Processing Complete!")
    print(f"  Processed: {stats['processed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total found: {stats['total']}")
    print(f"\nResults saved to: post_processed/")
    print(f"Format: post_processed/{{user_folder}}/analysis_result.json")
