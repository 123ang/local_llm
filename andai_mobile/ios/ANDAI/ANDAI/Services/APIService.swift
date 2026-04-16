import Foundation

enum APIError: Error, LocalizedError {
    case unauthorized
    case serverError(String)
    case networkError(Error)
    case decodingError
    
    var errorDescription: String? {
        switch self {
        case .unauthorized: return "Session expired. Please log in again."
        case .serverError(let msg): return msg
        case .networkError(let err): return err.localizedDescription
        case .decodingError: return "Failed to parse server response."
        }
    }
}

class APIService {
    static let shared = APIService()
    
    #if DEBUG
    private var baseURL = "http://localhost:8000/api"
    #else
    private var baseURL = "https://your-production-url.com/api"
    #endif
    
    private let session: URLSession
    
    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        session = URLSession(configuration: config)
    }
    
    func setBaseURL(_ url: String) {
        baseURL = url
    }
    
    // MARK: - Auth
    
    func login(email: String, password: String) async throws -> LoginResponse {
        let body = "username=\(email.urlEncoded)&password=\(password.urlEncoded)"
        return try await request("/auth/login", method: "POST", body: body.data(using: .utf8), contentType: "application/x-www-form-urlencoded")
    }
    
    func getMe() async throws -> User {
        return try await request("/auth/me")
    }
    
    // MARK: - Companies
    
    func getCompanies() async throws -> [Company] {
        return try await request("/companies")
    }
    
    func createCompany(name: String, description: String?) async throws -> Company {
        let payload: [String: Any] = ["name": name, "description": description ?? ""]
        return try await request("/companies", method: "POST", jsonBody: payload)
    }
    
    func updateCompany(id: Int, data: [String: Any]) async throws -> Company {
        return try await request("/companies/\(id)", method: "PATCH", jsonBody: data)
    }
    
    // MARK: - Users
    
    func getUsers(companyId: Int? = nil) async throws -> [UserItem] {
        let path = companyId != nil ? "/users?company_id=\(companyId!)" : "/users"
        return try await request(path)
    }
    
    func createUser(data: [String: Any]) async throws -> UserItem {
        return try await request("/users", method: "POST", jsonBody: data)
    }
    
    func updateUser(id: Int, data: [String: Any]) async throws -> UserItem {
        return try await request("/users/\(id)", method: "PATCH", jsonBody: data)
    }
    
    // MARK: - Documents
    
    func getDocuments(companyId: Int) async throws -> [Document] {
        return try await request("/documents/\(companyId)")
    }
    
    func uploadDocument(companyId: Int, fileURL: URL) async throws -> Document {
        let data = try Data(contentsOf: fileURL)
        let boundary = UUID().uuidString
        var body = Data()
        let filename = fileURL.lastPathComponent
        
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/pdf\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        return try await request("/documents/\(companyId)", method: "POST", body: body, contentType: "multipart/form-data; boundary=\(boundary)")
    }
    
    func deleteDocument(companyId: Int, docId: Int) async throws {
        let _: EmptyResponse = try await request("/documents/\(companyId)/\(docId)", method: "DELETE")
    }
    
    // MARK: - FAQ
    
    func getFAQ(companyId: Int) async throws -> [FAQItem] {
        return try await request("/faq/\(companyId)")
    }
    
    func createFAQ(companyId: Int, data: [String: Any]) async throws -> FAQItem {
        return try await request("/faq/\(companyId)", method: "POST", jsonBody: data)
    }
    
    func updateFAQ(companyId: Int, faqId: Int, data: [String: Any]) async throws -> FAQItem {
        return try await request("/faq/\(companyId)/\(faqId)", method: "PATCH", jsonBody: data)
    }
    
    func deleteFAQ(companyId: Int, faqId: Int) async throws {
        let _: EmptyResponse = try await request("/faq/\(companyId)/\(faqId)", method: "DELETE")
    }
    
    // MARK: - Datasets
    
    func getDatasets(companyId: Int) async throws -> [Dataset] {
        return try await request("/datasets/\(companyId)")
    }
    
    func getDatasetRows(companyId: Int, datasetId: Int, limit: Int = 100, offset: Int = 0) async throws -> DatasetRows {
        return try await request("/datasets/\(companyId)/\(datasetId)/rows?limit=\(limit)&offset=\(offset)")
    }
    
    // MARK: - Chat
    
    func getChatSessions(companyId: Int? = nil) async throws -> [ChatSession] {
        let path = companyId != nil ? "/chat/sessions?company_id=\(companyId!)" : "/chat/sessions"
        return try await request(path)
    }
    
    func getChatMessages(sessionId: Int) async throws -> [ChatMessage] {
        return try await request("/chat/sessions/\(sessionId)/messages")
    }
    
    func sendMessage(message: String, sessionId: Int? = nil, companyId: Int? = nil, sources: [String]? = nil, aiInsights: Bool = true, modelMode: String = "auto") async throws -> ChatResponse {
        var payload: [String: Any] = [
            "message": message,
            "ai_insights": aiInsights,
            "model_mode": modelMode
        ]
        if let sid = sessionId { payload["session_id"] = sid }
        if let cid = companyId { payload["company_id"] = cid }
        if let src = sources { payload["sources"] = src }
        return try await request("/chat", method: "POST", jsonBody: payload)
    }
    
    func deleteSession(sessionId: Int) async throws {
        let _: EmptyResponse = try await request("/chat/sessions/\(sessionId)", method: "DELETE")
    }
    
    // MARK: - Audit
    
    func getAuditLogs(companyId: Int? = nil, limit: Int = 100, offset: Int = 0) async throws -> [AuditLog] {
        var path = "/audit?"
        if let cid = companyId { path += "company_id=\(cid)&" }
        path += "limit=\(limit)&offset=\(offset)"
        return try await request(path)
    }
    
    // MARK: - Status
    
    func getStatus() async throws -> [String: Any] {
        return try await requestRaw("/status")
    }
    
    // MARK: - Private
    
    private func request<T: Decodable>(_ path: String, method: String = "GET", body: Data? = nil, contentType: String? = nil, jsonBody: [String: Any]? = nil) async throws -> T {
        var urlRequest = URLRequest(url: URL(string: baseURL + path)!)
        urlRequest.httpMethod = method
        
        if let token = AuthService.shared.token {
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let jsonBody = jsonBody {
            urlRequest.httpBody = try JSONSerialization.data(withJSONObject: jsonBody)
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        } else if let body = body {
            urlRequest.httpBody = body
            if let ct = contentType {
                urlRequest.setValue(ct, forHTTPHeaderField: "Content-Type")
            }
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }
        
        if httpResponse.statusCode == 401 {
            AuthService.shared.logout()
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode == 204 || data.isEmpty {
            if T.self == EmptyResponse.self {
                return EmptyResponse() as! T
            }
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let detail = json["detail"] {
                if let arr = detail as? [[String: Any]] {
                    let msg = arr.compactMap { $0["msg"] as? String }.joined(separator: ". ")
                    throw APIError.serverError(msg)
                }
                throw APIError.serverError("\(detail)")
            }
            throw APIError.serverError("Request failed with status \(httpResponse.statusCode)")
        }
        
        let decoder = JSONDecoder()
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError
        }
    }
    
    private func requestRaw(_ path: String) async throws -> [String: Any] {
        var urlRequest = URLRequest(url: URL(string: baseURL + path)!)
        if let token = AuthService.shared.token {
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let (data, _) = try await session.data(for: urlRequest)
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }
}

struct EmptyResponse: Decodable {}

extension String {
    var urlEncoded: String {
        addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? self
    }
}
