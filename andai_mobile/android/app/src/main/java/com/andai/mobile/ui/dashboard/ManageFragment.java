package com.andai.mobile.ui.dashboard;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.andai.mobile.R;
import com.andai.mobile.databinding.FragmentManageBinding;
import com.andai.mobile.ui.audit.AuditFragment;
import com.andai.mobile.ui.companies.CompaniesFragment;
import com.andai.mobile.ui.database.DatabaseFragment;
import com.andai.mobile.ui.documents.DocumentsFragment;
import com.andai.mobile.ui.faq.FAQFragment;
import com.andai.mobile.ui.users.UsersFragment;
import com.andai.mobile.utils.AuthManager;

public class ManageFragment extends Fragment {

    private FragmentManageBinding binding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentManageBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        AuthManager auth = AuthManager.getInstance(requireContext());
        boolean superAdmin = auth.isSuperAdmin();

        binding.cardCompanies.setVisibility(superAdmin ? View.VISIBLE : View.GONE);

        binding.cardDocuments.setOnClickListener(v -> openFragment(new DocumentsFragment()));
        binding.cardFaq.setOnClickListener(v -> openFragment(new FAQFragment()));
        binding.cardDatabase.setOnClickListener(v -> openFragment(new DatabaseFragment()));
        binding.cardCompanies.setOnClickListener(v -> openFragment(new CompaniesFragment()));
        binding.cardUsers.setOnClickListener(v -> openFragment(new UsersFragment()));
        binding.cardAudit.setOnClickListener(v -> openFragment(new AuditFragment()));
    }

    private void openFragment(Fragment fragment) {
        requireActivity()
                .getSupportFragmentManager()
                .beginTransaction()
                .replace(R.id.fragment_container, fragment)
                .addToBackStack(null)
                .commit();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
