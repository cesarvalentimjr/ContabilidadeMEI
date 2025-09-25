from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("/home/ubuntu/upload/MLGSAN122024.pdf")

print(result.document.export_to_markdown())

