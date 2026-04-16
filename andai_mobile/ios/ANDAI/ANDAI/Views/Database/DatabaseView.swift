import SwiftUI

struct DatabaseView: View {
    @EnvironmentObject var auth: AuthService
    @State private var datasets: [Dataset] = []
    @State private var isLoading = true
    @State private var selectedDataset: Dataset?
    @State private var rowData: DatasetRows?
    @State private var loadingRows = false
    
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Database").font(.system(size: 20, weight: .bold)).foregroundColor(.textPrimary)
                    Text("Browse your datasets and tables").font(.system(size: 13)).foregroundColor(.textSecondary)
                }
                Spacer()
            }
            .padding(16)
            .background(Color.bgCard)
            .overlay(Rectangle().fill(Color.border).frame(height: 1), alignment: .bottom)
            
            if isLoading {
                Spacer()
                ProgressView().tint(.appPrimary)
                Spacer()
            } else if datasets.isEmpty {
                Spacer()
                Image(systemName: "server.rack").font(.system(size: 42)).foregroundColor(.slate300)
                Text("No datasets available").font(.system(size: 15, weight: .medium)).foregroundColor(.slate400).padding(.top, 8)
                Text("Upload data via the web dashboard").font(.system(size: 13)).foregroundColor(.slate400).padding(.top, 2)
                Spacer()
            } else {
                List(datasets) { ds in
                    Button { viewRows(ds) } label: {
                        HStack(spacing: 12) {
                            ZStack {
                                RoundedRectangle(cornerRadius: 10).fill(Color.emerald50).frame(width: 44, height: 44)
                                Image(systemName: "server.rack").font(.system(size: 18)).foregroundColor(.emerald600)
                            }
                            VStack(alignment: .leading, spacing: 2) {
                                Text(ds.displayName.isEmpty ? ds.tableName : ds.displayName)
                                    .font(.system(size: 14, weight: .semibold)).foregroundColor(.textPrimary)
                                if let desc = ds.description, !desc.isEmpty {
                                    Text(desc).font(.system(size: 12)).foregroundColor(.textSecondary).lineLimit(1)
                                }
                                HStack(spacing: 10) {
                                    if let rc = ds.rowCount {
                                        HStack(spacing: 3) {
                                            Image(systemName: "tablecells").font(.system(size: 10))
                                            Text("\(rc) rows")
                                        }.font(.system(size: 11)).foregroundColor(.textSecondary)
                                    }
                                    if let cc = ds.columnCount {
                                        HStack(spacing: 3) {
                                            Image(systemName: "arrow.left.and.right").font(.system(size: 10))
                                            Text("\(cc) cols")
                                        }.font(.system(size: 11)).foregroundColor(.textSecondary)
                                    }
                                }
                            }
                            Spacer()
                            Image(systemName: "chevron.right").font(.system(size: 12)).foregroundColor(.slate300)
                        }
                        .padding(.vertical, 4)
                    }
                }
                .listStyle(.plain)
                .refreshable { await loadDatasets() }
            }
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .task { await loadDatasets() }
        .sheet(item: $selectedDataset) { ds in
            DatasetRowsSheet(dataset: ds, rows: rowData, isLoading: loadingRows)
        }
    }
    
    private func loadDatasets() async {
        guard let cid = auth.companyId else { return }
        datasets = (try? await APIService.shared.getDatasets(companyId: cid)) ?? []
        isLoading = false
    }
    
    private func viewRows(_ ds: Dataset) {
        selectedDataset = ds
        loadingRows = true
        rowData = nil
        Task {
            guard let cid = auth.companyId else { return }
            let data = try? await APIService.shared.getDatasetRows(companyId: cid, datasetId: ds.id, limit: 50)
            await MainActor.run {
                rowData = data
                loadingRows = false
            }
        }
    }
}

struct DatasetRowsSheet: View {
    let dataset: Dataset
    let rows: DatasetRows?
    let isLoading: Bool
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView().tint(.appPrimary)
                } else if let data = rows, !data.columns.isEmpty {
                    ScrollView(.horizontal) {
                        ScrollView(.vertical) {
                            VStack(spacing: 0) {
                                // Header
                                HStack(spacing: 0) {
                                    ForEach(data.columns, id: \.self) { col in
                                        Text(col)
                                            .font(.system(size: 11, weight: .semibold))
                                            .foregroundColor(.slate600)
                                            .frame(width: 130, alignment: .leading)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 6)
                                            .background(Color.slate100)
                                    }
                                }
                                
                                ForEach(Array(data.rows.prefix(50).enumerated()), id: \.offset) { i, row in
                                    HStack(spacing: 0) {
                                        ForEach(data.columns, id: \.self) { col in
                                            Text(row[col]?.stringValue ?? "")
                                                .font(.system(size: 11))
                                                .foregroundColor(.slate700)
                                                .frame(width: 130, alignment: .leading)
                                                .padding(.horizontal, 8)
                                                .padding(.vertical, 6)
                                                .lineLimit(1)
                                        }
                                    }
                                    .background(i % 2 == 1 ? Color.slate50 : Color.clear)
                                }
                            }
                        }
                    }
                } else {
                    Text("No data to display").foregroundColor(.slate400)
                }
            }
            .navigationTitle(dataset.displayName.isEmpty ? dataset.tableName : dataset.displayName)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
