from package.llm_postprocessor.io.csv_exporter import CSVExporter

stats = CSVExporter.export_all(
    post_processed_folder="post_processed",
    output_folder="csv_exports"
)

print(stats)
