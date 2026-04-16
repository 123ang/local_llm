package com.andai.mobile.ui.dashboard;

import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentOverviewBinding;
import com.andai.mobile.R;
import com.andai.mobile.models.ChatSession;
import com.andai.mobile.models.DatasetItem;
import com.andai.mobile.models.DocumentItem;
import com.andai.mobile.models.FaqItem;
import com.andai.mobile.models.User;
import com.andai.mobile.utils.AuthManager;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

public class OverviewFragment extends Fragment {

    private FragmentOverviewBinding binding;
    private final Gson gson = new Gson();

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentOverviewBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        AuthManager auth = AuthManager.getInstance(requireContext());
        User u = auth.getUser();
        String name = u != null && !TextUtils.isEmpty(u.fullName) ? u.fullName : "there";
        binding.tvWelcomeTitle.setText(getString(R.string.overview_welcome_title_fmt, name));
        loadStats(auth);
    }

    private void loadStats(AuthManager auth) {
        Integer companyId = auth.getCompanyId();
        if (companyId == null) {
            binding.tvStatDocuments.setText("0");
            binding.tvStatFaq.setText("0");
            binding.tvStatDatasets.setText("0");
            binding.tvStatSessions.setText("0");
            return;
        }

        binding.progress.setVisibility(View.VISIBLE);
        binding.scrollContent.setAlpha(0.5f);

        final int total = 4;
        AtomicInteger done = new AtomicInteger(0);
        final int[] counts = new int[4];

        Runnable finishBlock = () -> {
            if (done.incrementAndGet() >= total) {
                binding.progress.setVisibility(View.GONE);
                binding.scrollContent.setAlpha(1f);
                binding.tvStatDocuments.setText(String.valueOf(counts[0]));
                binding.tvStatFaq.setText(String.valueOf(counts[1]));
                binding.tvStatDatasets.setText(String.valueOf(counts[2]));
                binding.tvStatSessions.setText(String.valueOf(counts[3]));
            }
        };

        ApiClient api = ApiClient.getInstance();

        api.getDocuments(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (isAdded()) {
                    counts[0] = parseListSize(responseBody, DocumentItem.class);
                    finishBlock.run();
                }
            }

            @Override
            public void onError(String error) {
                if (isAdded()) finishBlock.run();
            }
        });

        api.getFAQ(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (isAdded()) {
                    counts[1] = parseListSize(responseBody, FaqItem.class);
                    finishBlock.run();
                }
            }

            @Override
            public void onError(String error) {
                if (isAdded()) finishBlock.run();
            }
        });

        api.getDatasets(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (isAdded()) {
                    counts[2] = parseListSize(responseBody, DatasetItem.class);
                    finishBlock.run();
                }
            }

            @Override
            public void onError(String error) {
                if (isAdded()) finishBlock.run();
            }
        });

        api.getChatSessions(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (isAdded()) {
                    counts[3] = parseListSize(responseBody, ChatSession.class);
                    finishBlock.run();
                }
            }

            @Override
            public void onError(String error) {
                if (isAdded()) finishBlock.run();
            }
        });
    }

    private <T> int parseListSize(String json, Class<T> itemClass) {
        try {
            Type type = TypeToken.getParameterized(List.class, itemClass).getType();
            List<T> list = gson.fromJson(json, type);
            return list != null ? list.size() : 0;
        } catch (JsonSyntaxException e) {
            return 0;
        }
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
