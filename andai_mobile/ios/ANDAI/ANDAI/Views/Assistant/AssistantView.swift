import SwiftUI

struct AssistantView: View {
    @EnvironmentObject var auth: AuthService
    @State private var sessions: [ChatSession] = []
    @State private var activeSessionId: Int?
    @State private var messages: [ChatMessage] = []
    @State private var input = ""
    @State private var isSending = false
    @State private var showSessions = false
    
    @State private var enableDatabase = true
    @State private var enableDocuments = true
    @State private var enableFaq = true
    @State private var aiInsights = true
    @State private var modelMode = "auto"
    
    private var enabledSources: [String] {
        var sources: [String] = []
        if enableDatabase { sources.append("database") }
        if enableDocuments { sources.append("documents") }
        if enableFaq { sources.append("faq") }
        return sources
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Button { showSessions = true } label: {
                    Image(systemName: "line.3.horizontal")
                        .font(.system(size: 18))
                        .foregroundColor(.textPrimary)
                }
                
                Spacer()
                
                Text(activeSessionId != nil ? (sessions.first { $0.id == activeSessionId }?.title ?? "Chat") : "New Chat")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.textPrimary)
                    .lineLimit(1)
                
                Spacer()
                
                Button { newChat() } label: {
                    Image(systemName: "plus")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundColor(.appPrimary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.bgCard)
            .overlay(
                Rectangle().fill(Color.border).frame(height: 1),
                alignment: .bottom
            )
            
            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    if messages.isEmpty {
                        emptyStateView
                    } else {
                        LazyVStack(spacing: 16) {
                            ForEach(messages) { msg in
                                MessageBubble(message: msg)
                            }
                            if isSending {
                                HStack(alignment: .top, spacing: 8) {
                                    botAvatar
                                    ProgressView()
                                        .padding(12)
                                        .background(Color.slate50)
                                        .cornerRadius(16)
                                    Spacer()
                                }
                            }
                            Color.clear.frame(height: 1).id("bottom")
                        }
                        .padding(16)
                    }
                }
                .onChange(of: messages.count) { _, _ in
                    withAnimation { proxy.scrollTo("bottom") }
                }
            }
            
            // Controls
            controlsBar
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .sheet(isPresented: $showSessions) {
            SessionsSheet(
                sessions: sessions,
                activeSessionId: activeSessionId,
                onSelect: { id in loadMessages(id) },
                onDelete: { id in deleteChat(id) },
                onNewChat: { newChat(); showSessions = false }
            )
        }
        .task { await loadSessions() }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Spacer().frame(height: 60)
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 42))
                .foregroundColor(.slate300)
            Text("How can I help you?")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.slate400)
            Text("Ask about your documents, data, or FAQ")
                .font(.system(size: 14))
                .foregroundColor(.slate400)
            
            VStack(spacing: 8) {
                ForEach([
                    "Which lecturers have the highest evaluation?",
                    "Show me student comments for a course",
                    "What data or tables do we have?",
                    "List staff by department"
                ], id: \.self) { q in
                    Button {
                        input = q
                    } label: {
                        Text(q)
                            .font(.system(size: 13))
                            .foregroundColor(.slate700)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(12)
                            .background(Color.slate100)
                            .cornerRadius(12)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.slate200, lineWidth: 1)
                            )
                    }
                }
            }
            .padding(.top, 16)
            .padding(.horizontal, 16)
        }
        .padding()
    }
    
    private var controlsBar: some View {
        VStack(spacing: 8) {
            // Source toggles
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    SourceToggle(label: "Database", icon: "server.rack", isOn: $enableDatabase, activeColor: .emerald600, activeBg: .emerald50)
                    SourceToggle(label: "Docs", icon: "doc.text", isOn: $enableDocuments, activeColor: .blue600, activeBg: .blue50)
                    SourceToggle(label: "FAQ", icon: "questionmark.circle", isOn: $enableFaq, activeColor: .amber600, activeBg: .amber50)
                    
                    Divider().frame(height: 24).padding(.horizontal, 4)
                    
                    SourceToggle(label: aiInsights && enabledSources.isEmpty ? "AI Only" : "AI Insights", icon: "lightbulb", isOn: $aiInsights, activeColor: .purple700, activeBg: .purple50)
                }
                .padding(.horizontal, 12)
            }
            
            // Model mode
            HStack(spacing: 8) {
                Text("Mode:")
                    .font(.system(size: 11))
                    .foregroundColor(.slate400)
                
                ForEach(["auto", "instant", "thinking"], id: \.self) { mode in
                    Button {
                        modelMode = mode
                    } label: {
                        HStack(spacing: 3) {
                            if mode == "instant" { Image(systemName: "bolt").font(.system(size: 9)) }
                            if mode == "thinking" { Image(systemName: "brain").font(.system(size: 9)) }
                            Text(mode.capitalized)
                                .font(.system(size: 11))
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(modelMode == mode ? modeColor(mode).0 : Color.bgCard)
                        .foregroundColor(modelMode == mode ? modeColor(mode).1 : .slate400)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(modelMode == mode ? modeColor(mode).1.opacity(0.5) : Color.slate200, lineWidth: 1)
                        )
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 12)
            
            // Input
            HStack(spacing: 8) {
                TextField("Ask about your data...", text: $input, axis: .vertical)
                    .lineLimit(1...4)
                    .padding(12)
                    .background(Color.bgMain)
                    .cornerRadius(16)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(Color.slate300, lineWidth: 1)
                    )
                    .disabled(isSending)
                    .onSubmit { sendMessage() }
                
                Button { sendMessage() } label: {
                    Image(systemName: "paperplane.fill")
                        .font(.system(size: 16))
                        .foregroundColor(.white)
                        .frame(width: 42, height: 42)
                        .background(input.trimmingCharacters(in: .whitespaces).isEmpty || isSending ? Color.appPrimary.opacity(0.5) : Color.appPrimary)
                        .cornerRadius(16)
                }
                .disabled(input.trimmingCharacters(in: .whitespaces).isEmpty || isSending)
            }
            .padding(.horizontal, 12)
        }
        .padding(.vertical, 8)
        .background(Color.bgCard)
        .overlay(
            Rectangle().fill(Color.border).frame(height: 1),
            alignment: .top
        )
    }
    
    private var botAvatar: some View {
        ZStack {
            Circle().fill(Color.red100).frame(width: 30, height: 30)
            Image(systemName: "cpu")
                .font(.system(size: 12))
                .foregroundColor(.appPrimary)
        }
    }
    
    private func modeColor(_ mode: String) -> (Color, Color) {
        switch mode {
        case "instant": return (.emerald50, .emerald600)
        case "thinking": return (.violet50, .violet600)
        default: return (.slate100, .slate700)
        }
    }
    
    // MARK: - Actions
    
    private func loadSessions() async {
        sessions = (try? await APIService.shared.getChatSessions(companyId: auth.companyId)) ?? []
    }
    
    private func loadMessages(_ sessionId: Int) {
        activeSessionId = sessionId
        showSessions = false
        Task {
            messages = (try? await APIService.shared.getChatMessages(sessionId: sessionId)) ?? []
        }
    }
    
    private func newChat() {
        activeSessionId = nil
        messages = []
    }
    
    private func deleteChat(_ id: Int) {
        Task {
            try? await APIService.shared.deleteSession(sessionId: id)
            if activeSessionId == id { newChat() }
            await loadSessions()
        }
    }
    
    private func sendMessage() {
        let text = input.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty, !isSending else { return }
        input = ""
        isSending = true
        
        let userMsg = ChatMessage(id: Int.random(in: 100000...999999), role: "user", content: text, sources: nil, createdAt: nil, modelTier: nil, responseTimeMs: nil)
        messages.append(userMsg)
        
        Task {
            do {
                let res = try await APIService.shared.sendMessage(
                    message: text,
                    sessionId: activeSessionId,
                    companyId: auth.companyId,
                    sources: enabledSources.isEmpty ? nil : enabledSources,
                    aiInsights: aiInsights,
                    modelMode: modelMode
                )
                if activeSessionId == nil {
                    activeSessionId = res.sessionId
                    await loadSessions()
                }
                let botMsg = ChatMessage(id: Int.random(in: 100000...999999), role: "assistant", content: res.message, sources: res.sources, createdAt: nil, modelTier: res.modelTier, responseTimeMs: res.responseTimeMs)
                await MainActor.run { messages.append(botMsg) }
            } catch {
                let errMsg = ChatMessage(id: Int.random(in: 100000...999999), role: "assistant", content: "Error: \(error.localizedDescription)", sources: nil, createdAt: nil, modelTier: nil, responseTimeMs: nil)
                await MainActor.run { messages.append(errMsg) }
            }
            await MainActor.run { isSending = false }
        }
    }
}

// MARK: - Subviews

struct SourceToggle: View {
    let label: String
    let icon: String
    @Binding var isOn: Bool
    let activeColor: Color
    let activeBg: Color
    
    var body: some View {
        Button { isOn.toggle() } label: {
            HStack(spacing: 4) {
                if isOn { Image(systemName: "checkmark").font(.system(size: 10, weight: .bold)) }
                Image(systemName: icon).font(.system(size: 11))
                Text(label).font(.system(size: 11, weight: .medium))
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(isOn ? activeBg : Color.bgCard)
            .foregroundColor(isOn ? activeColor : .slate400)
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(isOn ? activeColor.opacity(0.5) : Color.slate200, lineWidth: 1)
            )
        }
    }
}

struct MessageBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            if message.role == "assistant" {
                ZStack {
                    Circle().fill(Color.red100).frame(width: 30, height: 30)
                    Image(systemName: "cpu").font(.system(size: 12)).foregroundColor(.appPrimary)
                }
            }
            
            if message.role == "user" { Spacer(minLength: 40) }
            
            VStack(alignment: .leading, spacing: 6) {
                Text(message.content)
                    .font(.system(size: 14))
                    .foregroundColor(message.role == "user" ? .white : .textPrimary)
                    .lineSpacing(4)
                
                if message.role == "assistant" {
                    sourceBadges
                    metaInfo
                }
            }
            .padding(12)
            .background(message.role == "user" ? Color.appPrimary : Color.slate50)
            .cornerRadius(16, corners: message.role == "user" ? [.topLeading, .topTrailing, .bottomLeading] : [.topLeading, .topTrailing, .bottomTrailing])
            
            if message.role == "assistant" { Spacer(minLength: 40) }
            
            if message.role == "user" {
                ZStack {
                    Circle().fill(Color.slate200).frame(width: 30, height: 30)
                    Image(systemName: "person").font(.system(size: 12)).foregroundColor(.slate600)
                }
            }
        }
    }
    
    @ViewBuilder
    private var sourceBadges: some View {
        if let sources = message.sources {
            let hasFaq = (sources.faq?.count ?? 0) > 0
            let hasDocs = (sources.documents?.count ?? 0) > 0
            let hasDb = sources.database != nil
            
            if hasFaq || hasDocs || hasDb {
                FlowLayout(spacing: 4) {
                    if hasFaq {
                        Badge(icon: "questionmark.circle", text: "\(sources.faq!.count) FAQ", fg: .amber700, bg: .amber50, border: .amber200)
                    }
                    if hasDocs {
                        ForEach(Array(sources.documents!.enumerated()), id: \.offset) { _, doc in
                            Badge(icon: "doc.text", text: "\(doc.source ?? "")\(doc.page != nil ? ", p.\(doc.page!)" : "")", fg: .blue700, bg: .blue50, border: .blue200)
                        }
                    }
                    if hasDb {
                        Badge(icon: "server.rack", text: "\(sources.database!.rowCount ?? 0) rows", fg: .emerald700, bg: .emerald50, border: .emerald200)
                    }
                }
            }
        }
    }
    
    @ViewBuilder
    private var metaInfo: some View {
        if message.modelTier != nil || message.responseTimeMs != nil {
            HStack(spacing: 6) {
                if message.modelTier == "instant" {
                    HStack(spacing: 2) {
                        Image(systemName: "bolt").font(.system(size: 8))
                        Text("Instant").font(.system(size: 9, weight: .medium))
                    }
                    .foregroundColor(.emerald600)
                }
                if message.modelTier == "thinking" {
                    HStack(spacing: 2) {
                        Image(systemName: "brain").font(.system(size: 8))
                        Text("Thinking").font(.system(size: 9, weight: .medium))
                    }
                    .foregroundColor(.violet600)
                }
                if let ms = message.responseTimeMs {
                    Text(String(format: "%.1fs", Double(ms) / 1000))
                        .font(.system(size: 9))
                        .foregroundColor(.slate400)
                }
            }
        }
    }
}

struct Badge: View {
    let icon: String
    let text: String
    let fg: Color
    let bg: Color
    let border: Color
    
    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: icon).font(.system(size: 10))
            Text(text).font(.system(size: 10, weight: .medium)).lineLimit(1)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background(bg)
        .foregroundColor(fg)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(border, lineWidth: 1)
        )
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 4
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrangeSubviews(proposal: proposal, subviews: subviews)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrangeSubviews(proposal: proposal, subviews: subviews)
        for (index, subview) in subviews.enumerated() {
            if index < result.positions.count {
                subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x, y: bounds.minY + result.positions[index].y), proposal: .unspecified)
            }
        }
    }
    
    private func arrangeSubviews(proposal: ProposedViewSize, subviews: Subviews) -> (positions: [CGPoint], size: CGSize) {
        let maxWidth = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var totalHeight: CGFloat = 0
        
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > maxWidth && x > 0 {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            positions.append(CGPoint(x: x, y: y))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
            totalHeight = y + rowHeight
        }
        
        return (positions, CGSize(width: maxWidth, height: totalHeight))
    }
}

extension View {
    func cornerRadius(_ radius: CGFloat, corners: UIRectCorner) -> some View {
        clipShape(RoundedCorner(radius: radius, corners: corners))
    }
}

struct RoundedCorner: Shape {
    var radius: CGFloat
    var corners: UIRectCorner
    
    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(roundedRect: rect, byRoundingCorners: corners, cornerRadii: CGSize(width: radius, height: radius))
        return Path(path.cgPath)
    }
}

// MARK: - Sessions Sheet

struct SessionsSheet: View {
    let sessions: [ChatSession]
    let activeSessionId: Int?
    let onSelect: (Int) -> Void
    let onDelete: (Int) -> Void
    let onNewChat: () -> Void
    
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Button {
                    onNewChat()
                    dismiss()
                } label: {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("New Chat")
                            .font(.system(size: 14, weight: .semibold))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color.appPrimary)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
                .padding(16)
                
                List {
                    ForEach(sessions) { session in
                        Button {
                            onSelect(session.id)
                            dismiss()
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(session.title ?? "New chat")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(session.id == activeSessionId ? .appPrimary : .textPrimary)
                                        .lineLimit(1)
                                    Text("\(session.messageCount ?? 0) messages")
                                        .font(.system(size: 12))
                                        .foregroundColor(.textSecondary)
                                }
                                Spacer()
                            }
                            .padding(.vertical, 4)
                        }
                        .listRowBackground(session.id == activeSessionId ? Color.red50 : Color.clear)
                        .swipeActions(edge: .trailing) {
                            Button(role: .destructive) { onDelete(session.id) } label: {
                                Label("Delete", systemImage: "trash")
                            }
                        }
                    }
                }
                .listStyle(.plain)
            }
            .navigationTitle("Conversations")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark")
                            .foregroundColor(.textPrimary)
                    }
                }
            }
        }
    }
}
