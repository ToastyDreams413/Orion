#include <cmath>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

struct TrackInput {
    std::string id;
    std::string type;
    double dist_asset;
    double ttz;
    double directness;
    double speed;
    double uncertainty;
    double jamming;
    double thermal;
    double radiation;
    double size;
    double anomaly;
    double swarm;
    int transponder;
    int no_fly;
    int hazard;
    std::string source;
    std::string origin;
};

static double clamp(double x, double a, double b) { return std::max(a, std::min(b, x)); }

int main() {
    std::vector<TrackInput> tracks;
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        TrackInput t;
        ss >> t.id >> t.type >> t.dist_asset >> t.ttz >> t.directness >> t.speed >> t.uncertainty >> t.jamming
           >> t.thermal >> t.radiation >> t.size >> t.anomaly >> t.swarm >> t.transponder >> t.no_fly >> t.hazard
           >> t.source >> t.origin;
        if (!ss.fail()) tracks.push_back(t);
    }

    std::cout << std::fixed << std::setprecision(3);
    for (const auto& t : tracks) {
        double intent = 0.0;
        if (t.ttz >= 0 && t.ttz < 360) intent += clamp((360.0 - t.ttz) / 360.0, 0.0, 1.0) * 0.42;
        intent += clamp(t.directness, 0.0, 1.0) * 0.32;
        intent += t.no_fly ? 0.18 : 0.0;
        intent += t.hazard ? 0.07 : 0.0;
        if (!t.transponder) intent += 0.10;
        if ((t.type == "missile" || t.type == "asteroid" || t.type == "foreign_spaceship") && t.directness > 0.45) intent += 0.16;
        intent = clamp(intent, 0.0, 1.0);

        double capability = 0.0;
        capability += clamp(t.speed / 700.0, 0.0, 1.0) * 0.27;
        capability += clamp(t.size / 40.0, 0.0, 1.0) * 0.14;
        capability += clamp(t.thermal / 140.0, 0.0, 1.0) * 0.16;
        capability += clamp(t.radiation / 35.0, 0.0, 1.0) * 0.16;
        capability += clamp(t.swarm, 0.0, 1.0) * 0.08;
        if (t.type == "missile") capability += 0.34;
        if (t.type == "asteroid") capability += 0.32;
        if (t.type == "foreign_spaceship") capability += 0.24;
        if (t.type == "satellite" || t.type == "debris") capability += 0.10;
        capability = clamp(capability, 0.0, 1.0);

        double confidence = 1.0;
        confidence -= clamp(t.uncertainty / 210.0, 0.0, 1.0) * 0.30;
        confidence -= clamp(t.jamming, 0.0, 1.0) * 0.20;
        if (t.source == "fused" || t.source == "celestrak" || t.source == "nasa_jpl") confidence += 0.06;
        confidence = clamp(confidence, 0.10, 1.0);

        double env = 0.0;
        env += t.hazard ? 0.28 : 0.0;
        env += clamp(t.jamming, 0.0, 1.0) * 0.24;
        env += clamp(t.uncertainty / 240.0, 0.0, 1.0) * 0.16;
        if (t.origin == "extraterrestrial") env += 0.12;
        env = clamp(env, 0.0, 1.0);

        double anomaly = clamp((t.anomaly + 1.0) / 2.0, 0.0, 1.0);
        double raw_score = intent * 0.42 + capability * 0.32 + env * 0.10 + anomaly * 0.16;
        double final_score = clamp(raw_score * (0.72 + 0.28 * confidence), 0.0, 1.0);
        // Safety-oriented escalation: high-capability inbound objects should not decay to benign merely because they start far away.
        if ((t.type == "missile" || t.type == "asteroid" || t.type == "foreign_spaceship") && t.directness > 0.42) {
            final_score = std::max(final_score, clamp(0.48 + capability * 0.28 + intent * 0.22, 0.0, 1.0));
        }
        if (t.type == "missile" && t.ttz >= 0 && t.ttz < 480 && t.directness > 0.45) final_score = std::max(final_score, 0.86);
        if (t.type == "asteroid" && t.directness > 0.45 && (t.radiation > 10 || t.speed > 90)) final_score = std::max(final_score, 0.82);
        if (t.type == "foreign_spaceship" && t.directness > 0.50) final_score = std::max(final_score, 0.74);

        std::string level = "benign";
        if (final_score >= 0.72) level = "critical";
        else if (final_score >= 0.42) level = "suspicious";
        else if (final_score >= 0.20) level = "unknown";

        std::cout << t.id << " " << intent << " " << capability << " " << confidence << " " << env << " " << anomaly << " " << final_score << " " << level << "\n";
    }
    return 0;
}
