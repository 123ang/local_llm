import Foundation

struct User: Codable {
    let id: Int
    let email: String
    let fullName: String
    let role: String
    let companyId: Int?
    let companyName: String?
    
    var isAdmin: Bool { role == "admin" || role == "super_admin" }
    var isSuperAdmin: Bool { role == "super_admin" }
    
    enum CodingKeys: String, CodingKey {
        case id, email, role
        case fullName = "full_name"
        case companyId = "company_id"
        case companyName = "company_name"
    }
}

struct LoginResponse: Codable {
    let accessToken: String
    let user: User
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case user
    }
}

struct Company: Codable, Identifiable {
    let id: Int
    let name: String
    let description: String?
    let isActive: Bool?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, name, description
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

struct Document: Codable, Identifiable {
    let id: Int
    let filename: String
    let status: String
    let chunkCount: Int?
    let fileSize: Int?
    let uploadedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, filename, status
        case chunkCount = "chunk_count"
        case fileSize = "file_size"
        case uploadedAt = "uploaded_at"
    }
}

struct FAQItem: Codable, Identifiable {
    let id: Int
    let question: String
    let answer: String
    let isPublished: Bool
    let category: String?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, question, answer, category
        case isPublished = "is_published"
        case createdAt = "created_at"
    }
}

struct Dataset: Codable, Identifiable {
    let id: Int
    let tableName: String
    let displayName: String
    let description: String?
    let rowCount: Int?
    let columnCount: Int?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, description
        case tableName = "table_name"
        case displayName = "display_name"
        case rowCount = "row_count"
        case columnCount = "column_count"
        case createdAt = "created_at"
    }
}

struct DatasetRows: Codable {
    let columns: [String]
    let rows: [[String: AnyCodable]]
    let total: Int
}

struct AnyCodable: Codable {
    let value: Any
    
    init(_ value: Any) { self.value = value }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) { value = v }
        else if let v = try? container.decode(Int.self) { value = v }
        else if let v = try? container.decode(Double.self) { value = v }
        else if let v = try? container.decode(Bool.self) { value = v }
        else if container.decodeNil() { value = "null" }
        else { value = "" }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let v = value as? String { try container.encode(v) }
        else if let v = value as? Int { try container.encode(v) }
        else if let v = value as? Double { try container.encode(v) }
        else if let v = value as? Bool { try container.encode(v) }
        else { try container.encode("\(value)") }
    }
    
    var stringValue: String { "\(value)" }
}

struct ChatSession: Codable, Identifiable {
    let id: Int
    let title: String?
    let createdAt: String?
    let messageCount: Int?
    
    enum CodingKeys: String, CodingKey {
        case id, title
        case createdAt = "created_at"
        case messageCount = "message_count"
    }
}

struct ChatMessage: Codable, Identifiable {
    let id: Int
    let role: String
    let content: String
    let sources: ChatSources?
    let createdAt: String?
    let modelTier: String?
    let responseTimeMs: Int?
    
    enum CodingKeys: String, CodingKey {
        case id, role, content, sources
        case createdAt = "created_at"
        case modelTier = "model_tier"
        case responseTimeMs = "response_time_ms"
    }
}

struct ChatSources: Codable {
    let faq: [FAQSource]?
    let documents: [DocSource]?
    let database: DatabaseSource?
}

struct FAQSource: Codable {
    let question: String?
    let answer: String?
}

struct DocSource: Codable {
    let source: String?
    let page: Int?
    let content: String?
}

struct DatabaseSource: Codable {
    let query: String?
    let rowCount: Int?
    let result: [AnyCodable]?
    
    enum CodingKeys: String, CodingKey {
        case query, result
        case rowCount = "row_count"
    }
}

struct ChatResponse: Codable {
    let message: String
    let sessionId: Int
    let sources: ChatSources?
    let modelTier: String?
    let responseTimeMs: Int?
    
    enum CodingKeys: String, CodingKey {
        case message, sources
        case sessionId = "session_id"
        case modelTier = "model_tier"
        case responseTimeMs = "response_time_ms"
    }
}

struct AuditLog: Codable, Identifiable {
    let id: Int
    let action: String
    let resourceType: String?
    let resourceId: Int?
    let userEmail: String?
    let details: String?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, action, details
        case resourceType = "resource_type"
        case resourceId = "resource_id"
        case userEmail = "user_email"
        case createdAt = "created_at"
    }
}

struct UserItem: Codable, Identifiable {
    let id: Int
    let email: String
    let fullName: String
    let role: String
    let isActive: Bool?
    let companyId: Int?
    let companyName: String?
    
    enum CodingKeys: String, CodingKey {
        case id, email, role
        case fullName = "full_name"
        case isActive = "is_active"
        case companyId = "company_id"
        case companyName = "company_name"
    }
}
