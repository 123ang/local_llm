import SwiftUI

struct FAQListView: View {
    @EnvironmentObject var auth: AuthService
    @State private var faqs: [FAQItem] = []
    @State private var isLoading = true
    @State private var showForm = false
    @State private var editingFAQ: FAQItem?
    
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading) {
                    Text("FAQ").font(.system(size: 20, weight: .bold)).foregroundColor(.textPrimary)
                    Text("Manage frequently asked questions").font(.system(size: 13)).foregroundColor(.textSecondary)
                }
                Spacer()
                if auth.isAdmin {
                    Button {
                        editingFAQ = nil
                        showForm = true
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "plus")
                            Text("Add")
                        }
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 8)
                        .background(Color.appPrimary)
                        .cornerRadius(10)
                    }
                }
            }
            .padding(16)
            .background(Color.bgCard)
            .overlay(Rectangle().fill(Color.border).frame(height: 1), alignment: .bottom)
            
            if isLoading {
                Spacer()
                ProgressView().tint(.appPrimary)
                Spacer()
            } else if faqs.isEmpty {
                Spacer()
                Image(systemName: "questionmark.circle").font(.system(size: 42)).foregroundColor(.slate300)
                Text("No FAQ items yet").font(.system(size: 15, weight: .medium)).foregroundColor(.slate400).padding(.top, 8)
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(faqs) { faq in
                            faqCard(faq)
                        }
                    }
                    .padding(16)
                }
                .refreshable { await loadFAQs() }
            }
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .task { await loadFAQs() }
        .sheet(isPresented: $showForm) {
            FAQFormSheet(editingFAQ: editingFAQ, companyId: auth.companyId ?? 0) {
                Task { await loadFAQs() }
            }
        }
    }
    
    private func faqCard(_ faq: FAQItem) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 8).fill(Color.amber50).frame(width: 32, height: 32)
                    Image(systemName: "questionmark.circle").font(.system(size: 16)).foregroundColor(.amber600)
                }
                Spacer()
                if let cat = faq.category, !cat.isEmpty {
                    Text(cat).font(.system(size: 11)).foregroundColor(.textSecondary)
                }
                Text(faq.isPublished ? "Published" : "Draft")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(faq.isPublished ? .emerald700 : .slate500)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(faq.isPublished ? Color.emerald50 : Color.slate100)
                    .cornerRadius(4)
            }
            
            Text(faq.question).font(.system(size: 14, weight: .semibold)).foregroundColor(.textPrimary)
            Text(faq.answer).font(.system(size: 13)).foregroundColor(.textSecondary).lineLimit(3).lineSpacing(3)
            
            if auth.isAdmin {
                Divider()
                HStack(spacing: 20) {
                    Button {
                        editingFAQ = faq
                        showForm = true
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "pencil").font(.system(size: 12))
                            Text("Edit").font(.system(size: 13, weight: .medium))
                        }
                        .foregroundColor(.blue600)
                    }
                    
                    Button {
                        deleteFAQ(faq)
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "trash").font(.system(size: 12))
                            Text("Delete").font(.system(size: 13, weight: .medium))
                        }
                        .foregroundColor(.red600)
                    }
                }
            }
        }
        .padding(16)
        .background(Color.bgCard)
        .cornerRadius(16)
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.border, lineWidth: 1))
    }
    
    private func loadFAQs() async {
        guard let cid = auth.companyId else { return }
        faqs = (try? await APIService.shared.getFAQ(companyId: cid)) ?? []
        isLoading = false
    }
    
    private func deleteFAQ(_ faq: FAQItem) {
        guard let cid = auth.companyId else { return }
        Task {
            try? await APIService.shared.deleteFAQ(companyId: cid, faqId: faq.id)
            await loadFAQs()
        }
    }
}

struct FAQFormSheet: View {
    let editingFAQ: FAQItem?
    let companyId: Int
    let onSave: () -> Void
    
    @Environment(\.dismiss) var dismiss
    @State private var question = ""
    @State private var answer = ""
    @State private var category = ""
    @State private var isPublished = true
    @State private var isSaving = false
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Question") {
                    TextEditor(text: $question)
                        .frame(minHeight: 60)
                }
                Section("Answer") {
                    TextEditor(text: $answer)
                        .frame(minHeight: 100)
                }
                Section {
                    TextField("Category", text: $category)
                    Toggle("Published", isOn: $isPublished)
                }
            }
            .navigationTitle(editingFAQ != nil ? "Edit FAQ" : "New FAQ")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        save()
                    } label: {
                        if isSaving { ProgressView().tint(.appPrimary) }
                        else { Text("Save").fontWeight(.semibold) }
                    }
                    .disabled(question.isEmpty || answer.isEmpty || isSaving)
                }
            }
            .onAppear {
                if let faq = editingFAQ {
                    question = faq.question
                    answer = faq.answer
                    category = faq.category ?? ""
                    isPublished = faq.isPublished
                }
            }
        }
    }
    
    private func save() {
        isSaving = true
        let data: [String: Any] = [
            "question": question,
            "answer": answer,
            "category": category.isEmpty ? "" : category,
            "is_published": isPublished
        ]
        Task {
            do {
                if let faq = editingFAQ {
                    _ = try await APIService.shared.updateFAQ(companyId: companyId, faqId: faq.id, data: data)
                } else {
                    _ = try await APIService.shared.createFAQ(companyId: companyId, data: data)
                }
                onSave()
                await MainActor.run { dismiss() }
            } catch {}
            await MainActor.run { isSaving = false }
        }
    }
}
