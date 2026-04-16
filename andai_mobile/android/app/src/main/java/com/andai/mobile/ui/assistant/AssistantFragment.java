package com.andai.mobile.ui.assistant;

import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentAssistantBinding;
import com.andai.mobile.models.ChatMessage;
import com.andai.mobile.models.ChatResponse;
import com.andai.mobile.models.ChatSession;
import com.andai.mobile.utils.AuthManager;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class AssistantFragment extends Fragment {

    private FragmentAssistantBinding binding;
    private MessageAdapter adapter;
    private final Gson gson = new Gson();

    private Integer currentSessionId;
    private String modelMode = "auto";
    private boolean sending;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentAssistantBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        adapter = new MessageAdapter(requireContext());
        binding.rvMessages.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvMessages.setAdapter(adapter);

        binding.toggleModelMode.addOnButtonCheckedListener((group, checkedId, isChecked) -> {
            if (!isChecked) return;
            if (checkedId == R.id.btnModeAuto) {
                modelMode = "auto";
            } else if (checkedId == R.id.btnModeInstant) {
                modelMode = "instant";
            } else if (checkedId == R.id.btnModeThinking) {
                modelMode = "thinking";
            }
        });

        binding.btnSessions.setOnClickListener(v -> showSessionsDialog());
        binding.btnNewChat.setOnClickListener(v -> startNewChat());
        binding.btnSend.setOnClickListener(v -> sendCurrentMessage());

        binding.etMessage.setOnEditorActionListener((tv, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                sendCurrentMessage();
                return true;
            }
            return false;
        });

        binding.chipSuggest1.setOnClickListener(c -> fillSuggestion(binding.chipSuggest1.getText().toString()));
        binding.chipSuggest2.setOnClickListener(c -> fillSuggestion(binding.chipSuggest2.getText().toString()));
        binding.chipSuggest3.setOnClickListener(c -> fillSuggestion(binding.chipSuggest3.getText().toString()));

        updateEmptyState();
        binding.tvChatTitle.setText(R.string.chat_new_conversation);
    }

    private void fillSuggestion(String text) {
        binding.etMessage.setText(text);
        binding.etMessage.setSelection(text.length());
    }

    private void startNewChat() {
        currentSessionId = null;
        adapter.setItems(new ArrayList<>());
        binding.tvChatTitle.setText(R.string.chat_new_conversation);
        updateEmptyState();
    }

    private void showSessionsDialog() {
        AuthManager auth = AuthManager.getInstance(requireContext());
        Integer companyId = auth.getCompanyId();
        ApiClient.getInstance().getChatSessions(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                try {
                    Type type = new TypeToken<List<ChatSession>>() {
                    }.getType();
                    List<ChatSession> sessions = gson.fromJson(responseBody, type);
                    if (sessions == null) sessions = new ArrayList<>();
                    if (sessions.isEmpty()) {
                        Toast.makeText(requireContext(), R.string.chat_no_sessions, Toast.LENGTH_SHORT).show();
                        return;
                    }
                    String[] titles = new String[sessions.size()];
                    for (int i = 0; i < sessions.size(); i++) {
                        ChatSession s = sessions.get(i);
                        titles[i] = TextUtils.isEmpty(s.title) ? ("Session " + s.id) : s.title;
                    }
                    requireActivity().runOnUiThread(() ->
                            new MaterialAlertDialogBuilder(requireContext())
                                    .setTitle(R.string.chat_sessions)
                                    .setItems(titles, (d, which) -> loadSession(sessions.get(which).id, titles[which]))
                                    .setNegativeButton(android.R.string.cancel, null)
                                    .show());
                } catch (JsonSyntaxException e) {
                    Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onError(String error) {
                if (isAdded()) {
                    Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void loadSession(int sessionId, String title) {
        currentSessionId = sessionId;
        binding.tvChatTitle.setText(title);
        binding.layoutTyping.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getChatMessages(sessionId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                requireActivity().runOnUiThread(() -> binding.layoutTyping.setVisibility(View.GONE));
                try {
                    Type type = new TypeToken<List<ChatMessage>>() {
                    }.getType();
                    List<ChatMessage> list = gson.fromJson(responseBody, type);
                    List<DisplayMessage> out = new ArrayList<>();
                    if (list != null) {
                        for (ChatMessage cm : list) {
                            DisplayMessage dm = new DisplayMessage(cm.role, cm.content);
                            dm.sources = cm.sources;
                            dm.modelTier = cm.modelTier;
                            dm.responseTimeMs = cm.responseTimeMs;
                            dm.createdAt = cm.createdAt;
                            out.add(dm);
                        }
                    }
                    requireActivity().runOnUiThread(() -> {
                        adapter.setItems(out);
                        updateEmptyState();
                        scrollToBottom();
                    });
                } catch (JsonSyntaxException e) {
                    requireActivity().runOnUiThread(() ->
                            Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show());
                }
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                requireActivity().runOnUiThread(() -> {
                    binding.layoutTyping.setVisibility(View.GONE);
                    Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
                });
            }
        });
    }

    private void sendCurrentMessage() {
        if (sending) return;
        CharSequence cs = binding.etMessage.getText();
        String text = cs != null ? cs.toString().trim() : "";
        if (TextUtils.isEmpty(text)) return;

        AuthManager auth = AuthManager.getInstance(requireContext());
        Integer companyId = auth.getCompanyId();
        if (companyId == null) {
            Toast.makeText(requireContext(), R.string.error_no_company, Toast.LENGTH_SHORT).show();
            return;
        }

        binding.etMessage.setText("");
        DisplayMessage userMsg = new DisplayMessage("user", text);
        adapter.add(userMsg);
        updateEmptyState();
        scrollToBottom();

        JsonObject body = new JsonObject();
        body.addProperty("message", text);
        body.addProperty("company_id", companyId);
        if (currentSessionId != null) {
            body.addProperty("session_id", currentSessionId);
        }

        JsonArray sources = new JsonArray();
        if (binding.chipSourceDatabase.isChecked()) {
            sources.add("database");
        }
        if (binding.chipSourceDocs.isChecked()) {
            sources.add("documents");
        }
        if (binding.chipSourceFaq.isChecked()) {
            sources.add("faq");
        }
        body.add("sources", sources);
        body.addProperty("ai_insights", binding.chipAiInsights.isChecked());
        body.addProperty("model_mode", modelMode);

        sending = true;
        binding.layoutTyping.setVisibility(View.VISIBLE);

        ApiClient.getInstance().sendMessage(body.toString(), new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                requireActivity().runOnUiThread(() -> {
                    binding.layoutTyping.setVisibility(View.GONE);
                    sending = false;
                });
                try {
                    ChatResponse resp = gson.fromJson(responseBody, ChatResponse.class);
                    if (resp == null) return;
                    requireActivity().runOnUiThread(() -> {
                        currentSessionId = resp.sessionId;
                        DisplayMessage bot = new DisplayMessage("assistant", resp.message);
                        bot.sources = resp.sources;
                        bot.modelTier = resp.modelTier;
                        bot.responseTimeMs = resp.responseTimeMs;
                        adapter.add(bot);
                        updateEmptyState();
                        scrollToBottom();
                    });
                } catch (JsonSyntaxException e) {
                    requireActivity().runOnUiThread(() ->
                            Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show());
                }
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                requireActivity().runOnUiThread(() -> {
                    binding.layoutTyping.setVisibility(View.GONE);
                    sending = false;
                    Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
                });
            }
        });
    }

    private void updateEmptyState() {
        boolean empty = adapter == null || adapter.getItemCount() == 0;
        binding.layoutEmpty.setVisibility(empty ? View.VISIBLE : View.GONE);
    }

    private void scrollToBottom() {
        binding.rvMessages.post(() -> {
            int n = adapter.getItemCount();
            if (n > 0) {
                binding.rvMessages.scrollToPosition(n - 1);
            }
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
