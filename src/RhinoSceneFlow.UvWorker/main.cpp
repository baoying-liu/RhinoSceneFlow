#include "xatlas.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <vector>

template<class T> T read(std::istream& f) { T v{}; if(!f.read(reinterpret_cast<char*>(&v),sizeof(v)))throw std::runtime_error("Truncated input"); return v; }
template<class T> void write(std::ostream& f,T v) { if(!f.write(reinterpret_cast<char*>(&v),sizeof(v)))throw std::runtime_error("Output write failed"); }
bool progress(xatlas::ProgressCategory c,int percent,void*) {
    static std::mutex output;std::lock_guard<std::mutex> lock(output);
    if(percent%10==0)std::cout<<"{\"stage\":\""<<xatlas::StringForEnum(c)<<"\",\"percent\":"<<percent<<"}"<<std::endl;
    return true;
}
int main(int argc,char** argv) {
    try {
        if(argc!=3)throw std::runtime_error("Expected input and output filenames");
        std::ifstream in(argv[1],std::ios::binary);
        if(read<uint32_t>(in)!=0x31565553)throw std::runtime_error("Invalid input format");
        auto nv=read<uint32_t>(in),ni=read<uint32_t>(in);
        if(nv<3||nv>2000000||ni<3||ni>18000000||ni%3)throw std::runtime_error("Unsupported mesh size");
        std::vector<float> positions(size_t(nv)*3);std::vector<uint32_t> indices(ni);
        float lo[3]={INFINITY,INFINITY,INFINITY},hi[3]={-INFINITY,-INFINITY,-INFINITY};
        for(size_t i=0;i<positions.size();++i) {
            positions[i]=read<float>(in);if(!std::isfinite(positions[i]))throw std::runtime_error("Nonfinite vertex");
            lo[i%3]=std::min(lo[i%3],positions[i]);hi[i%3]=std::max(hi[i%3],positions[i]);
        }
        for(auto& i:indices){i=read<uint32_t>(in);if(i>=nv)throw std::runtime_error("Invalid index");}
        if(in.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Unexpected trailing input");
        std::unique_ptr<xatlas::Atlas,decltype(&xatlas::Destroy)> atlas(xatlas::Create(),xatlas::Destroy);
        xatlas::SetProgressCallback(atlas.get(),progress,nullptr);
        xatlas::MeshDecl mesh;mesh.vertexPositionData=positions.data();mesh.vertexPositionStride=12;mesh.vertexCount=nv;
        mesh.indexData=indices.data();mesh.indexCount=ni;mesh.indexFormat=xatlas::IndexFormat::UInt32;
        auto error=xatlas::AddMesh(atlas.get(),mesh);
        if(error!=xatlas::AddMeshError::Success)throw std::runtime_error(xatlas::StringForEnum(error));
        xatlas::ChartOptions chart;chart.maxIterations=2;chart.fixWinding=true;
        xatlas::PackOptions pack;pack.texelsPerUnit=2048/std::max({hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2],.001f});
        pack.resolution=0;pack.padding=1;pack.rotateCharts=false;pack.rotateChartsToAxis=false;
        xatlas::Generate(atlas.get(),chart,pack);
        if(atlas->meshCount!=1||atlas->chartCount==0||atlas->texelsPerUnit<=0)throw std::runtime_error("No atlas produced");
        auto& result=atlas->meshes[0];if(result.indexCount!=ni)throw std::runtime_error("Face correspondence changed");
        std::ofstream out(argv[2],std::ios::binary|std::ios::trunc);
        write(out,uint32_t(0x32565553));write(out,result.vertexCount);write(out,result.indexCount);write(out,atlas->chartCount);
        for(uint32_t i=0;i<result.vertexCount;++i){auto& v=result.vertexArray[i];if(v.chartIndex<0)throw std::runtime_error("Unparameterized vertex");
            write(out,v.xref);write(out,v.chartIndex);write(out,double(v.uv[0]/atlas->texelsPerUnit));write(out,double(v.uv[1]/atlas->texelsPerUnit));}
        for(uint32_t i=0;i<result.indexCount;++i)write(out,result.indexArray[i]);
        std::cout<<"{\"stage\":\"completed\",\"charts\":"<<atlas->chartCount<<"}"<<std::endl;
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<std::endl;return 1;}
}
