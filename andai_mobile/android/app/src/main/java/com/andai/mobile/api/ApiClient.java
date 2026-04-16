package com.andai.mobile.api;

import android.os.Handler;
import android.os.Looper;

import com.andai.mobile.BuildConfig;
import com.andai.mobile.utils.AuthManager;

import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class ApiClient {
    private static final String BASE_URL = BuildConfig.API_BASE_URL;
    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");
    private static final MediaType FORM = MediaType.parse("application/x-www-form-urlencoded");

    private static ApiClient instance;
    private final OkHttpClient client;
    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private AuthManager authManager;

    public interface ApiCallback {
        void onSuccess(String responseBody);
        void onError(String error);
    }

    public static synchronized ApiClient getInstance() {
        if (instance == null) {
            instance = new ApiClient();
        }
        return instance;
    }

    private ApiClient() {
        client = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(120, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();
    }

    public void setAuthManager(AuthManager am) {
        this.authManager = am;
    }

    // MARK: - Auth

    public void login(String email, String password, ApiCallback callback) {
        String body = "username=" + encode(email) + "&password=" + encode(password);
        post("/auth/login", RequestBody.create(body, FORM), callback);
    }

    // MARK: - Companies

    public void getCompanies(ApiCallback callback) { get("/companies", callback); }

    public void createCompany(String json, ApiCallback callback) {
        post("/companies", RequestBody.create(json, JSON), callback);
    }

    public void updateCompany(int id, String json, ApiCallback callback) {
        patch("/companies/" + id, RequestBody.create(json, JSON), callback);
    }

    // MARK: - Users

    public void getUsers(Integer companyId, ApiCallback callback) {
        String path = companyId != null ? "/users?company_id=" + companyId : "/users";
        get(path, callback);
    }

    public void createUser(String json, ApiCallback callback) {
        post("/users", RequestBody.create(json, JSON), callback);
    }

    public void updateUser(int id, String json, ApiCallback callback) {
        patch("/users/" + id, RequestBody.create(json, JSON), callback);
    }

    // MARK: - Documents

    public void getDocuments(int companyId, ApiCallback callback) {
        get("/documents/" + companyId, callback);
    }

    /**
     * Multipart PDF upload to POST /documents/{companyId}.
     */
    public void uploadDocument(int companyId, byte[] pdfBytes, String filename, ApiCallback callback) {
        RequestBody fileBody = RequestBody.create(pdfBytes, MediaType.parse("application/pdf"));
        MultipartBody body = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", filename != null ? filename : "upload.pdf", fileBody)
                .build();
        postMultipart("/documents/" + companyId, body, callback);
    }

    public void deleteDocument(int companyId, int docId, ApiCallback callback) {
        delete("/documents/" + companyId + "/" + docId, callback);
    }

    // MARK: - FAQ

    public void getFAQ(int companyId, ApiCallback callback) {
        get("/faq/" + companyId, callback);
    }

    public void createFAQ(int companyId, String json, ApiCallback callback) {
        post("/faq/" + companyId, RequestBody.create(json, JSON), callback);
    }

    public void updateFAQ(int companyId, int faqId, String json, ApiCallback callback) {
        patch("/faq/" + companyId + "/" + faqId, RequestBody.create(json, JSON), callback);
    }

    public void deleteFAQ(int companyId, int faqId, ApiCallback callback) {
        delete("/faq/" + companyId + "/" + faqId, callback);
    }

    // MARK: - Datasets

    public void getDatasets(int companyId, ApiCallback callback) {
        get("/datasets/" + companyId, callback);
    }

    public void getDatasetRows(int companyId, int datasetId, int limit, int offset, ApiCallback callback) {
        get("/datasets/" + companyId + "/" + datasetId + "/rows?limit=" + limit + "&offset=" + offset, callback);
    }

    // MARK: - Chat

    public void getChatSessions(Integer companyId, ApiCallback callback) {
        String path = companyId != null ? "/chat/sessions?company_id=" + companyId : "/chat/sessions";
        get(path, callback);
    }

    public void getChatMessages(int sessionId, ApiCallback callback) {
        get("/chat/sessions/" + sessionId + "/messages", callback);
    }

    public void sendMessage(String json, ApiCallback callback) {
        post("/chat", RequestBody.create(json, JSON), callback);
    }

    public void deleteSession(int sessionId, ApiCallback callback) {
        delete("/chat/sessions/" + sessionId, callback);
    }

    // MARK: - Audit

    public void getAuditLogs(Integer companyId, int limit, int offset, ApiCallback callback) {
        StringBuilder path = new StringBuilder("/audit?");
        if (companyId != null) path.append("company_id=").append(companyId).append("&");
        path.append("limit=").append(limit).append("&offset=").append(offset);
        get(path.toString(), callback);
    }

    // MARK: - Status

    public void getStatus(ApiCallback callback) { get("/status", callback); }

    // MARK: - HTTP Methods

    private void get(String path, ApiCallback callback) {
        executor.execute(() -> {
            try {
                Request.Builder builder = new Request.Builder().url(BASE_URL + path);
                addAuth(builder);
                Response response = client.newCall(builder.build()).execute();
                handleResponse(response, callback);
            } catch (IOException e) {
                postError(callback, e.getMessage());
            }
        });
    }

    private void post(String path, RequestBody body, ApiCallback callback) {
        executor.execute(() -> {
            try {
                Request.Builder builder = new Request.Builder().url(BASE_URL + path).post(body);
                addAuth(builder);
                Response response = client.newCall(builder.build()).execute();
                handleResponse(response, callback);
            } catch (IOException e) {
                postError(callback, e.getMessage());
            }
        });
    }

    private void patch(String path, RequestBody body, ApiCallback callback) {
        executor.execute(() -> {
            try {
                Request.Builder builder = new Request.Builder().url(BASE_URL + path).patch(body);
                addAuth(builder);
                Response response = client.newCall(builder.build()).execute();
                handleResponse(response, callback);
            } catch (IOException e) {
                postError(callback, e.getMessage());
            }
        });
    }

    private void delete(String path, ApiCallback callback) {
        executor.execute(() -> {
            try {
                Request.Builder builder = new Request.Builder().url(BASE_URL + path).delete();
                addAuth(builder);
                Response response = client.newCall(builder.build()).execute();
                handleResponse(response, callback);
            } catch (IOException e) {
                postError(callback, e.getMessage());
            }
        });
    }

    private void postMultipart(String path, MultipartBody body, ApiCallback callback) {
        executor.execute(() -> {
            try {
                Request.Builder builder = new Request.Builder()
                        .url(BASE_URL + path)
                        .post(body);
                addAuth(builder);
                Response response = client.newCall(builder.build()).execute();
                handleResponse(response, callback);
            } catch (IOException e) {
                postError(callback, e.getMessage());
            }
        });
    }

    private void addAuth(Request.Builder builder) {
        if (authManager != null && authManager.getToken() != null) {
            builder.addHeader("Authorization", "Bearer " + authManager.getToken());
        }
    }

    private void handleResponse(Response response, ApiCallback callback) throws IOException {
        String body = response.body() != null ? response.body().string() : "";
        if (response.isSuccessful()) {
            mainHandler.post(() -> callback.onSuccess(body));
        } else {
            String errorMsg = "Request failed";
            try {
                com.google.gson.JsonObject json = com.google.gson.JsonParser.parseString(body).getAsJsonObject();
                if (json.has("detail")) {
                    errorMsg = json.get("detail").getAsString();
                }
            } catch (Exception ignored) {}
            String finalMsg = errorMsg;
            mainHandler.post(() -> callback.onError(finalMsg));
        }
    }

    private void postError(ApiCallback callback, String msg) {
        mainHandler.post(() -> callback.onError(msg != null ? msg : "Network error"));
    }

    private String encode(String s) {
        try {
            return java.net.URLEncoder.encode(s, "UTF-8");
        } catch (Exception e) {
            return s;
        }
    }
}
