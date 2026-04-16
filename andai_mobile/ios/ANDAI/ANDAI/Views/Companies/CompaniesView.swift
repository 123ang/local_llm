import SwiftUI

struct CompaniesView: View {
    @EnvironmentObject var auth: AuthService
    @State private var companies: [Company] = []
    @State private var isLoading = true
    @State private var showForm = false
    @State private var editingCompany: Company?
    
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Companies").font(.system(size: 20, weight: .bold)).foregroundColor(.textPrimary)
                    Text("Manage platform tenants").font(.system(size: 13)).foregroundColor(.textSecondary)
                }
                Spacer()
                Button {
                    editingCompany = nil
                    showForm = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "plus")
                        Text("Add")
                    }
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 14).padding(.vertical, 8)
                    .background(Color.appPrimary).cornerRadius(10)
                }
            }
            .padding(16)
            .background(Color.bgCard)
            .overlay(Rectangle().fill(Color.border).frame(height: 1), alignment: .bottom)
            
            if isLoading {
                Spacer(); ProgressView().tint(.appPrimary); Spacer()
            } else {
                List(companies) { c in
                    HStack(spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 10).fill(Color.appPrimaryLight).frame(width: 44, height: 44)
                            Image(systemName: "building.2").font(.system(size: 18)).foregroundColor(.appPrimary)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(c.name).font(.system(size: 14, weight: .semibold)).foregroundColor(.textPrimary)
                            if let desc = c.description, !desc.isEmpty {
                                Text(desc).font(.system(size: 12)).foregroundColor(.textSecondary).lineLimit(1)
                            }
                            Text(c.isActive == true ? "Active" : "Inactive")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(c.isActive == true ? .emerald700 : .red600)
                                .padding(.horizontal, 6).padding(.vertical, 2)
                                .background(c.isActive == true ? Color.emerald50 : Color.red50)
                                .cornerRadius(4)
                        }
                        Spacer()
                        Button {
                            editingCompany = c
                            showForm = true
                        } label: {
                            Image(systemName: "pencil").font(.system(size: 14)).foregroundColor(.blue600)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
                .refreshable { await loadCompanies() }
            }
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .task { await loadCompanies() }
        .sheet(isPresented: $showForm) {
            CompanyFormSheet(editing: editingCompany) {
                Task { await loadCompanies() }
            }
        }
    }
    
    private func loadCompanies() async {
        companies = (try? await APIService.shared.getCompanies()) ?? []
        isLoading = false
    }
}

struct CompanyFormSheet: View {
    let editing: Company?
    let onSave: () -> Void
    @Environment(\.dismiss) var dismiss
    @State private var name = ""
    @State private var desc = ""
    @State private var isSaving = false
    
    var body: some View {
        NavigationStack {
            Form {
                TextField("Company Name", text: $name)
                Section("Description") {
                    TextEditor(text: $desc).frame(minHeight: 80)
                }
            }
            .navigationTitle(editing != nil ? "Edit Company" : "New Company")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        save()
                    } label: {
                        if isSaving { ProgressView() } else { Text("Save").fontWeight(.semibold) }
                    }
                    .disabled(name.isEmpty || isSaving)
                }
            }
            .onAppear {
                if let c = editing { name = c.name; desc = c.description ?? "" }
            }
        }
    }
    
    private func save() {
        isSaving = true
        Task {
            do {
                if let c = editing {
                    _ = try await APIService.shared.updateCompany(id: c.id, data: ["name": name, "description": desc])
                } else {
                    _ = try await APIService.shared.createCompany(name: name, description: desc.isEmpty ? nil : desc)
                }
                onSave()
                await MainActor.run { dismiss() }
            } catch {}
            await MainActor.run { isSaving = false }
        }
    }
}
