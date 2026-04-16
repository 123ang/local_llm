package com.andai.mobile.utils;

import android.content.Context;
import android.content.SharedPreferences;

import com.andai.mobile.models.User;
import com.google.gson.Gson;

public class AuthManager {
    private static final String PREFS_NAME = "andai_prefs";
    private static final String KEY_TOKEN = "auth_token";
    private static final String KEY_USER = "user_data";
    private static final String KEY_COMPANY_ID = "selected_company_id";

    private static AuthManager instance;
    private final SharedPreferences prefs;
    private final Gson gson = new Gson();

    private User currentUser;
    private String token;
    private Integer selectedCompanyId;

    public static synchronized AuthManager getInstance(Context context) {
        if (instance == null) {
            instance = new AuthManager(context.getApplicationContext());
        }
        return instance;
    }

    private AuthManager(Context context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        loadSession();
    }

    private void loadSession() {
        token = prefs.getString(KEY_TOKEN, null);
        String userJson = prefs.getString(KEY_USER, null);
        if (userJson != null) {
            currentUser = gson.fromJson(userJson, User.class);
        }
        int cid = prefs.getInt(KEY_COMPANY_ID, -1);
        selectedCompanyId = cid != -1 ? cid : (currentUser != null ? currentUser.companyId : null);
    }

    public void saveSession(String token, User user) {
        this.token = token;
        this.currentUser = user;
        this.selectedCompanyId = user.companyId;
        prefs.edit()
                .putString(KEY_TOKEN, token)
                .putString(KEY_USER, gson.toJson(user))
                .putInt(KEY_COMPANY_ID, user.companyId != null ? user.companyId : -1)
                .apply();
    }

    public void logout() {
        token = null;
        currentUser = null;
        selectedCompanyId = null;
        prefs.edit().clear().apply();
    }

    public boolean isLoggedIn() {
        return token != null && currentUser != null;
    }

    public String getToken() { return token; }
    public User getUser() { return currentUser; }

    public boolean isAdmin() { return currentUser != null && currentUser.isAdmin(); }
    public boolean isSuperAdmin() { return currentUser != null && currentUser.isSuperAdmin(); }

    public Integer getCompanyId() {
        return selectedCompanyId != null ? selectedCompanyId : (currentUser != null ? currentUser.companyId : null);
    }

    public void setCompanyId(int id) {
        selectedCompanyId = id;
        prefs.edit().putInt(KEY_COMPANY_ID, id).apply();
    }
}
