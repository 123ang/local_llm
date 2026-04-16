import SwiftUI
import UniformTypeIdentifiers

struct DocumentsView: View {
    @EnvironmentObject var auth: AuthService
    @State private var documents: [Document] = []
    @State private var isLoading = true
    @State private var showFilePicker = false
    @State private var isUploading = false
    @State private var alertMessage = ""
    @State private var showAlert = false
    
    var body: some View {
        VStack(spacing: 0) {
            headerBar
            
            if isLoading {
                Spacer()
                ProgressView().tint(.appPrimary)
                Spacer()
            } else if documents.isEmpty {
                emptyState
            } else {
                List {
                    ForEach(documents) { doc in
                        documentRow(doc)
                    }
                    .onDelete { indexSet in
                        if let i = indexSet.first {
                            deleteDoc(documents[i])
                        }
                    }
                }
                .listStyle(.plain)
                .refreshable { await loadDocuments() }
            }
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .task { await loadDocuments() }
        .fileImporter(isPresented: $showFilePicker, allowedContentTypes: [UTType.pdf], allowsMultipleSelection: false) { result in
            handleFileSelection(result)
        }
        .alert("", isPresented: $showAlert) {
            Button("OK") {}
        } message: {
            Text(alertMessage)
        }
    }
    
    private var headerBar: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("Documents")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(.textPrimary)
                Text("Upload and manage PDF documents")
                    .font(.system(size: 13))
                    .foregroundColor(.textSecondary)
            }
            Spacer()
            if auth.isAdmin {
                Button {
                    showFilePicker = true
                } label: {
                    HStack(spacing: 4) {
                        if isUploading {
                            ProgressView().tint(.white).scaleEffect(0.8)
                        } else {
                            Image(systemName: "icloud.and.arrow.up")
                            Text("Upload")
                        }
                    }
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(Color.appPrimary)
                    .cornerRadius(10)
                }
                .disabled(isUploading)
            }
        }
        .padding(16)
        .background(Color.bgCard)
        .overlay(Rectangle().fill(Color.border).frame(height: 1), alignment: .bottom)
    }
    
    private func documentRow(_ doc: Document) -> some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 10).fill(Color.red50).frame(width: 44, height: 44)
                Image(systemName: "doc.text").font(.system(size: 20)).foregroundColor(.appPrimary)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(doc.filename)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.textPrimary)
                    .lineLimit(1)
                HStack(spacing: 8) {
                    Text(doc.status)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(statusColor(doc.status))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(statusBg(doc.status))
                        .cornerRadius(4)
                    if let chunks = doc.chunkCount, chunks > 0 {
                        Text("\(chunks) chunks")
                            .font(.system(size: 11))
                            .foregroundColor(.textSecondary)
                    }
                }
            }
            Spacer()
        }
        .padding(.vertical, 4)
    }
    
    private var emptyState: some View {
        VStack(spacing: 12) {
            Spacer()
            Image(systemName: "doc.text")
                .font(.system(size: 42))
                .foregroundColor(.slate300)
            Text("No documents uploaded yet")
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(.slate400)
            Text("Upload PDF files to get started")
                .font(.system(size: 13))
                .foregroundColor(.slate400)
            Spacer()
        }
    }
    
    private func statusColor(_ status: String) -> Color {
        switch status {
        case "processed", "completed": return .emerald700
        case "processing": return .amber700
        case "failed": return .red600
        default: return .slate600
        }
    }
    
    private func statusBg(_ status: String) -> Color {
        switch status {
        case "processed", "completed": return .emerald50
        case "processing": return .amber50
        case "failed": return .red50
        default: return .slate100
        }
    }
    
    private func loadDocuments() async {
        guard let cid = auth.companyId else { return }
        documents = (try? await APIService.shared.getDocuments(companyId: cid)) ?? []
        isLoading = false
    }
    
    private func handleFileSelection(_ result: Result<[URL], Error>) {
        guard case .success(let urls) = result, let url = urls.first else { return }
        guard url.startAccessingSecurityScopedResource() else { return }
        defer { url.stopAccessingSecurityScopedResource() }
        
        isUploading = true
        Task {
            do {
                guard let cid = auth.companyId else { return }
                _ = try await APIService.shared.uploadDocument(companyId: cid, fileURL: url)
                await loadDocuments()
                alertMessage = "Document uploaded successfully."
            } catch {
                alertMessage = error.localizedDescription
            }
            await MainActor.run {
                isUploading = false
                showAlert = true
            }
        }
    }
    
    private func deleteDoc(_ doc: Document) {
        guard let cid = auth.companyId else { return }
        Task {
            try? await APIService.shared.deleteDocument(companyId: cid, docId: doc.id)
            await loadDocuments()
        }
    }
}
